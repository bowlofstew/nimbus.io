package main

import (
	"encoding/json"
	"fmt"

	"github.com/pebbe/zmq4"

	"fog"
)

type Message map[string]string

type ackOnlyMessageHandler func(Message)

// NewWriterSocketHandler returns a function suitable for use as a handler
// by zmq.Reactor
func NewWriterSocketHandler(writerSocket *zmq4.Socket) func(zmq4.State) error {

	// these messages get only and ack, not a reply
	var ackOnlyMessageMap = map[string]ackOnlyMessageHandler{
		"ping": handlePing,
		"resilient-server-handshake": handleHandshake,
		"resilient-server-signoff":   handleSignoff}

	return func(_ zmq4.State) error {
		rawMessage, err := writerSocket.RecvMessage(0)
		if err != nil {
			return fmt.Errorf("RecvMessage %s", err)
		}

		var message Message
		err = json.Unmarshal([]byte(rawMessage[0]), &message)
		if err != nil {
			return fmt.Errorf("Unmarshal %s", err)
		}

		reply := Message{
			"message-type":  "resilient-server-ack",
			"message-id":    message["message-id"],
			"incoming-type": message["message-type"],
			"accepted":      "true"}

		marshalledReply, err := json.Marshal(reply)
		if err != nil {
			return fmt.Errorf("Marshal %s", err)
		}

		_, err = writerSocket.SendMessage([]string{string(marshalledReply)})
		if err != nil {
			return fmt.Errorf("SendMessage %s", err)
		}

		/* ---------------------------------------------------------------
		** 2014-05-21 dougfort:
		** The python version of ResiliantServer maintains a dict of
		** "client-address" for sending replies, but IMO we don't need
		** that here because every message contains "client-address"
		** so we can decouple the reply.
		** -------------------------------------------------------------*/
		handler, ok := ackOnlyMessageMap[message["message-type"]]
		if ok {
			handler(message)
			return nil
		}

		fog.Debug("writer-socket-handler received %s from %s %s",
			message["message-type"], message["client-address"],
			message["message-id"])

		/*
				body := make([][]byte, len(rawMessage)-1)
				for i := 1; i < len(rawMessage); i++ {
					body[i-1] = []byte(rawMessage[i])
				}
				messageChan <- MessageWithBody{Message: message, Body: body}
			}
		*/
		return nil
	}
}

func handlePing(_ Message) {

}

func handleHandshake(message Message) {
	fog.Info("handshake from %s", message["client-address"])
}

func handleSignoff(message Message) {
	fog.Info("signoff from   %s", message["client-address"])
}
