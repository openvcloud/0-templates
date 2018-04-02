import requests, argparse, sys, packet, time, uuid, os


class Packet:
    def __init__(self, token):
        self.manager = packet.Manager(auth_token=token)
        self.project = self.manager.list_projects()[0].id

    def get_available_facility(self, plan):
        facilities = self.manager.list_facilities()
        for facility in facilities:
            try:
                if self.manager.validate_capacity([(facility.code, plan, 1)]):
                    return facility.code
            except:
                pass
        else:
            return None

    def create_machine(self, hostname, plan='baremetal_0'):
        facility = self.get_available_facility(plan=plan)
        device = self.manager.create_device(
            project_id=self.project,
            hostname=hostname,
            plan=plan,
            operating_system='ubuntu_16_04',
            facility=facility
        )
        return device

    def wait_for_ipaddress(self, deviceId, timeout=300):
        for _ in range(timeout):
            device = self.manager.get_device(deviceId)
            if device.state == 'active':
                return device.ip_addresses[0]['address']
            else:
                time.sleep(1)
        else:
            raise RuntimeError('packet machine creation timeout')

    def delete_devices(self, hostname):
        devices = self.manager.list_devices(self.project)
        for device in devices:
            if hostname in device.hostname:
                self.manager.call_api('devices/%s' % device.id, type='DELETE')

    def delete_ssh_keys(self, label):
        ssh_keys = self.manager.list_ssh_keys()
        for ssh_key in ssh_keys:
            if label in ssh_key.label:
                self.manager.call_api('ssh-keys/%s' % ssh_key.id, type='DELETE')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=str, required=True)
    parser.add_argument("-t", "--packet_token", type=str)
    parser.add_argument("-k", "--job_key", type=str)

    options = parser.parse_args()

    if options.action == 'create_machine':
        packet_client = Packet(token=options.packet_token)
        hostname = 'ovc-template-{}-travis'.format(options.job_key)

        with open(os.path.join(os.environ['HOME'], '.ssh/id_rsa.pub'), 'r') as f:
            sshkey = f.read().strip()

        ssh_label = 'sshkey-{}'.format(options.job_key)
        packet_client.manager.create_ssh_key(ssh_label, sshkey)

        device = packet_client.create_machine(hostname)
        device_ipaddress = packet_client.wait_for_ipaddress(device.id)
        os.system('printf "{}" >> /tmp/device_ipaddress.txt'.format(device_ipaddress))

        print(device_ipaddress)

    elif options.action == 'delete_machine':
        packet_client = Packet(token=options.packet_token)
        packet_client.delete_devices(options.job_key)
        packet_client.delete_ssh_keys(options.job_key)
