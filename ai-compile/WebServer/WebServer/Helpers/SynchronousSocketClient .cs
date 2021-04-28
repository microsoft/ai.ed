using webserver.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace webserver.Helpers
{
    public class SynchronousSocketClient
    {
        public static string StartClient(IPAddress serverIp, int serverPort, int predAtk, Code code)
        {
            // Data buffer for incoming data.  
            byte[] bytes = new byte[8192];

            // Connect to a remote device.  
            try
            {
                // Establish the remote endpoint for the socket.  
                // This example uses port 11000 on the local computer.  
                IPEndPoint remoteEP = new IPEndPoint(serverIp, serverPort);

                // Create a TCP/IP  socket.  
                Socket sender = new Socket(serverIp.AddressFamily,
                    SocketType.Stream, ProtocolType.Tcp);

                // Connect the socket to the remote endpoint. Catch any errors.  
                try
                {
                    sender.Connect(remoteEP);

                    Console.WriteLine("Socket connected to {0}",
                        sender.RemoteEndPoint.ToString());

                    // Encode the data string into a byte array.  
                    byte[] msg = Encoding.ASCII.GetBytes(predAtk.ToString() + "\n");

                    // Send the data through the socket.  
                    int bytesSent = sender.Send(msg);

                    msg = Encoding.ASCII.GetBytes(code.source);
                    bytesSent = sender.Send(msg);
                    
                    // Receive the response from the remote device.  
                    int bytesRec = sender.Receive(bytes);
                    string response = Encoding.ASCII.GetString(bytes, 0, bytesRec);
                    Console.WriteLine("Echoed test = {0}", response);

                    // Release the socket.  
                    sender.Shutdown(SocketShutdown.Both);
                    sender.Close();

                    return response;

                }
                catch (ArgumentNullException ane)
                {
                    Console.WriteLine("ArgumentNullException : {0}", ane.ToString());
                }
                catch (SocketException se)
                {
                    Console.WriteLine("SocketException : {0}", se.ToString());
                }
                catch (Exception e)
                {
                    Console.WriteLine("Unexpected exception : {0}", e.ToString());
                }

            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }
            return "";
        }
    }
}
