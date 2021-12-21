from volumio_webthing.volumio_webthing import run_server
from volumio_webthing.app import App
from string import Template
from typing import Dict


PACKAGENAME = 'volumio_webthing'
ENTRY_POINT = "volumio"
DESCRIPTION = "A web connected volumio"


UNIT_TEMPLATE = Template('''
[Unit]
Description=$packagename
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$entrypoint --command listen --port $port --volumio_base_uri $volumio_base_uri --event_listener_port $event_listener_port
SyslogIdentifier=$packagename
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
''')


def parse_credentials(credentials) -> Dict[str, str]:
    user_pwd_list = {}
    for part in credentials.split(" "):
        idx = part.index(":")
        if idx > 0:
            user = part[:idx]
            pwd = part[idx+1:]
            part[user] = pwd
            print("user '" + user + "'")
            print("pwd '" + pwd + "'")
            user_pwd_list[user] = pwd
    return user_pwd_list



class InternetApp(App):

    def do_add_argument(self, parser):
        parser.add_argument('--volumio_base_uri', metavar='volumio_base_uri', required=True, type=str, help='the volumio base uri such as http://10.1.33.30:3000')
        parser.add_argument('--event_listener_port', metavar='event_listener_port', required=False, type=int, default=9090, help='the event listener port')

    def do_additional_listen_example_params(self):
        return "--volumio_base_uri http://10.1.33.30:3000"

    def do_process_command(self, command:str, port: int, verbose: bool, args) -> bool:
        if command == 'listen' and (args.volumio_base_uri is not None):
            run_server(port, self.description, args.volumio_base_uri, args.event_listener_port)
            return True
        elif args.command == 'register' and (args.volumio_base_uri is not None):
            print("register " + self.packagename + " on port " + str(args.port))
            unit = UNIT_TEMPLATE.substitute(packagename=self.packagename,
                                            entrypoint=self.entrypoint,
                                            port=port,
                                            volumio_base_uri=args.volumio_base_uri,
                                            event_listener_port=args.event_listener_port,
                                            verbose=verbose)
            self.unit.register(port, unit)
            return True
        else:
            return False

def main():
    InternetApp(PACKAGENAME, ENTRY_POINT, DESCRIPTION).handle_command()


if __name__ == '__main__':
    main()


