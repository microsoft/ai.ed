using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using webserver.Helpers;
using webserver.Models;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc;
using Newtonsoft.Json.Linq;

namespace webserver.Controllers
{

    [Route("api/[controller]")]
    [ApiController]
    public class ValuesController : ControllerBase
    {

        private IHostingEnvironment _hostEnvironment;
        private ConfigOptions _configOptions;

        public ValuesController(IHostingEnvironment environment, ConfigOptions configOptions)
        {
            _hostEnvironment = environment;
            _configOptions = configOptions;
        }
        // GET api/values Probably Don't need to implement get 
        [HttpGet]
        public ActionResult<IEnumerable<string>> Get()
        {
            return new string[] { "hello-world API" };
        }

        
        // POST api/values
        [HttpPost]
        public ActionResult Post([FromBody] Code code)
        {
            try
            {
                // Connect to the socket server and get the fix for given code
                string response = SynchronousSocketClient.StartClient(_configOptions.ipAddress, _configOptions.port, Constants.predAtK, code);
                return Created("", response);
                            }
            catch (Exception ex)
            {
                var message = NotFound("some error occured" + ex.ToString());
                return message;
            }
        }

    }
}
