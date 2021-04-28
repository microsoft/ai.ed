using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading.Tasks;

namespace webserver.Models
{
    public class ConfigOptions
    {
        public IPAddress ipAddress { get; set; }
        public int port { get; set; }
    }
}
