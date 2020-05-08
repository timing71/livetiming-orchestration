from autobahn.twisted.component import run
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.types import RegisterOptions, PublishOptions
from livetiming import configure_sentry_twisted, load_env, make_component
from livetiming.network import Channel, Message, MessageClass, Realm, RPC, authenticatedService
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.logger import Logger


@authenticatedService
class Directory(ApplicationSession):
    log = Logger()

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.services = {}
        self.publish_options = PublishOptions(retain=True)

    def removeService(self, errorArgs, serviceUUID):
        self.log.info("Removing dead service {}".format(serviceUUID))
        if serviceUUID in self.services:
            self.services.pop(serviceUUID)
        self.broadcastServicesList()

    def checkLiveness(self):
        count = len(self.services)
        if count > 0:
            self.log.info("Checking liveness of {} service(s)".format(count))
        for service in list(self.services.keys()):
            _ = self.call(RPC.LIVENESS_CHECK.format(service)).addErrback(self.removeService, serviceUUID=service)

    def broadcastServicesList(self):
        self.publish(
            Channel.DIRECTORY,
            Message(MessageClass.DIRECTORY_LISTING, list(self.services.values()), retain=True).serialise(),
            options=self.publish_options
        )

    def getServicesList(self, includeHidden=False):
        return [s for s in list(self.services.values()) if includeHidden or not s.get('hidden')]

    @inlineCallbacks
    def onJoin(self, details):
        self.log.info("Session ready")

        yield self.register(self.getServicesList, RPC.GET_DIRECTORY_LISTING)
        yield self.subscribe(self.onControlMessage, Channel.CONTROL)
        self.log.debug("Subscribed to control channel")
        yield self.publish(Channel.CONTROL, Message(MessageClass.INITIALISE_DIRECTORY).serialise())
        self.log.debug("Published init message")
        self.broadcastServicesList()

        liveness = task.LoopingCall(self.checkLiveness)
        liveness.start(10)

        broadcast = task.LoopingCall(self.broadcastServicesList)
        broadcast.start(60)

    def onControlMessage(self, message):
        msg = Message.parse(message)
        self.log.debug("Received message {msg}", msg=msg)
        if (msg.msgClass == MessageClass.SERVICE_REGISTRATION):
            reg = msg.payload
            self.services[reg["uuid"]] = reg
            self.broadcastServicesList()

    def onDisconnect(self):
        self.log.info("Disconnected")
        if reactor.running:
            reactor.stop()


configure_sentry_twisted()


def main():
    load_env()
    Logger().info("Starting directory service...")

    component = make_component(Directory)
    run(component)


if __name__ == '__main__':
    main()