import sys
import snapchat
def send_to(username, password, recipient, fname):
    with open(fname) as f:
        data = f.read()
    connection = snapchat.Snapchat(username, password)
    connection.connect()
    media_id = connection.upload(data, snapchat.Snap.Type.IMAGE)
    connection.send_to(recipient, media_id, snapchat.Snap.Type.IMAGE)

    # Update and find the id used by the server for our upload
    connection.update()
    # The server will set the client_id of the snap to 'media_id + recipient + number'
    snap = filter(lambda snap : isinstance(snap, snapchat.SentSnap) and snap.client_id.startswith(media_id)\
                  , connection.snaps)[0]
    # the ID has the form <blah>s on the sender and <blah>r on the recipient.
    print "snap uploaded. Sender id:%s Recipient id:%s" % (snap.id, snap.id[:-1]+'r')

if __name__ == "__main__":
    username = sys.argv[1]
    password = sys.argv[2]
    recipient = sys.argv[3]
    fname = sys.argv[4]
    send_to(username, password, recipient, fname)
