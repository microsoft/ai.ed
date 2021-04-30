using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Threading.Tasks;
using webserver.Helpers;
using webserver.Models;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace webserver
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddMvc().SetCompatibilityVersion(CompatibilityVersion.Version_2_1);
            IPHostEntry ipHostInfo = Dns.GetHostEntry(Dns.GetHostName());
            // Get first ipv4 address
            int found = 0;
            for (int i = 0; i < ipHostInfo.AddressList.Length; i++)
            {
                var addressFamily = ipHostInfo.AddressList[i].AddressFamily;
                if (addressFamily.ToString() == ProtocolFamily.InterNetwork.ToString())
                {
                    found = i;
                    break;
                }

            }
            IPAddress ipAddress = ipHostInfo.AddressList[found];
            Action<ConfigOptions> options = (opt =>
            {
                opt.ipAddress = ipAddress;
                opt.port = 11000;
            });
            services.Configure(options);
            services.AddSingleton(resolver => resolver.GetRequiredService<IOptions<ConfigOptions>>().Value);
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IHostingEnvironment env, ConfigOptions configOptions)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            app.UseMvc();

            // Start the ML socketserver as a background process
            IPAddress ipAddress = configOptions.ipAddress;
            string port = configOptions.port.ToString();
            string ip = ipAddress.ToString();
            string path = Path.Combine(env.ContentRootPath, "Helpers");
            path = Path.Combine(path, "Brain.py");
            string pyMacerPath = Path.Combine(env.ContentRootPath, "..\\..\\PyMacer");
            var runCmd = new RunCmd(true);

            var result = runCmd.Run(path, pyMacerPath, "MACER", ip, port);
        }
    }
}
