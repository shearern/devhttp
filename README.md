devhttp
=======

A Development HTTP Server.

Have you ever wanted to quickly setup an HTTP server for your development
project?  I'm not talking about quickly starting a service that will
eventually be hosted by a web server, but rather a quick and dirty web
server that you to get going quick without putting thge time into
setting up a more flexible and profession framework like Django or Flask.
These types of projects will never hit production, but may be invaluable
in the development process.

This library provides a method to quickly create web servers that are
hosted from a Python process.


Usage
=====

Define your server object by instantiating DevelopmentHttpServer

    def microserver():

        srv = DevelopmentHttpServer()

        srv.add_static(...)
        srv.add_dynamic(...)

        srv.serve_forever('127.0.0.1', 8080)

Static Served Content
---------------------

Static files can be served up simply by specifying where the files is
to serve.

    srv.add_static('favicon.ico', os.path.join(project, 'static', 'favicon.ico')

Parameters are:

 - **url**: URL to the content for the server to know when to serve this
    file.
 - **path**: Path to the file on the disk to serve when the browser
    requests this URL.
 - **content_type**: Specify the content type to return (else, guessed)

You can also add a whole directory of assets at once:

    srv.add_static_dir('prefix', '/var/mystatics')

Which will find every file under /var/mystatics, and add it with a URL
prefixed with 'prefix'.


Other Non-Python Assets
-----------------------

In addition to static files that can be served to the clients, there may
be other files that the server may need access to.  Typically, these are
tempaltes that will be used to generate the content.  Use add_asset()
to define this type of content to include.

    srv.add_asset(name, path)

Where name is a token used to retrieve the file from the assets parameter
in a dynamic content callable, and path is the path to the file.


Dynamic Served Content
----------------------

Dynamic content can be generated by python callables (either a function
or an object with a __call__() method.

    def index_page(request, server, assets):
        return "<html><h1>My Page</h1></html>"

    srv.add_dynamic('index', index_page)

It's important to note that the callable can be invoked multiple times
in parallel since the HTTP server is threaded.  It must be thread safe.
However, the dynamic code will be passed a reference to the server which
can be assumed thread safe due to the ServerWrapper which protects the
Server class attributes with a thread lock.  Therfore, store your shared
state in the server class (inherited from DevelopmentHttpServer).


Saving Statics
--------------

I often want to encapsulate my static content into a Python module so
that I don't need to ship the static files in my Python packages.  To
support this pattern, the DevelopmentHttpServer supports saving the
static files content to a Python module (zipped, and base 64 encoded),
which can be loaded directly.


    srv = DevelopmentHttpServer()

    srv.add_static(...)

    # Save to Python module
    src.save_assets_module('my_statics.py', var_name='MY_STATICS')

    # Load statics back in
    import my_statics
    src.load_assets_module(my_statics.MY_STATICS)
