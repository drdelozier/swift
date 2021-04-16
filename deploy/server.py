import os

from fabric import Connection
from fabric.transfer import Transfer

# class
class Server(object):

    def __init__(self, host, user, key_filename):
        assert type(host) is str
        assert type(user) is str
        assert type(key_filename) is str
        assert os.path.exists(key_filename)
        self.connection = Connection(host=host,
                                     user=user,
                                     connect_kwargs={"key_filename":key_filename})
        self.transfer = Transfer(self.connection)

    def local(self, command, stdin="", hide=True):
        result = self.connection.local(command, hide=hide)
        return result.stdout, result.stderr
    
    def run(self, command, stdin="", hide=True):
        result = self.connection.run(command, hide=hide)
        return result.stdout, result.stderr

    def sudo(self, command, stdin="", hide=True):
        result = self.connection.sudo(command, hide=hide)
        return result.stdout, result.stderr

    def get(self, remote, local=None, preserve_mode=True):
        self.transfer.get(remote, local, preserve_mode)
        return None

    def put(self, local, remote=None, preserve_mode=True):
        self.transfer.put(local, remote, preserve_mode)
        return None

    def get_operating_system(self):
        stdout, _ = self.run("uname -s")
        return stdout.strip()

    # apt packages

    def get_installed_apt_packages(self):
        stdout, _ = self.run("apt list --installed")
        packages = stdout.strip().split("\n")
        packages = [p.split("/")[0] for p in packages if "/" in p]
        return packages

    def apt_package_is_installed(self, package):
        return package in self.get_installed_apt_packages()

    def update_apt_packages(self):
        self.sudo("apt-get -y update", hide=False)

    def install_apt_package(self, package, force=False):
        assert type(package) is str
        if self.apt_package_is_installed(package) and not force:
            print(package, "already installed.")
        else:
            self.sudo("apt-get -y install {p}".format(p=package))

    def install_apt_packages(self, packages, force=False):
        assert type(packages) is list
        for package in packages:
            self.install_apt_package(package, force)

    # processes

    def get_running_processes(self):
        stdout, _ = self.run("ps -aeo pid,command", hide=True)
        processes = [p for p in stdout.split("\n") if p != 'COMMAND' and p != '']
        return processes

    def process_is_running(self, name):
        return any([process for process in self.get_running_processes() if name in process])

    def get_running_process_id(self, name):
        processes = [process for process in self.get_running_processes() if name in process]
        if (len(processes) == 0):
            return 0
        process=processes[0].strip().split(' ')
        print(process)
        pid=int(process[0])
        print(pid)
        return(pid)

    # standard tool versions

    def get_python3_version(self):
        stdout, _ = self.run("python3 --version", hide=True)
        version = stdout.strip().replace("Python ","")
        return version

    def get_pip3_version(self):
        stdout, _ = self.run("pip3 --version", hide=True)
        result = stdout.strip().replace("(","").replace(")","").split(" ")
        result = [r for r in result if r[0] in "0123456789"]
        version = '/'.join(result)
        return version

    def get_git_version(self):
        stdout, _ = self.run("git --version", hide=True)
        version = stdout.strip().replace("git version ","")
        return version

    # pip packages

    def get_installed_pip3_packages(self, with_versions=False):
        stdout, _ = self.run("pip3 list --format freeze")
        packages = stdout.strip().split("\n")
        if with_versions==False:
            packages = [ p.split("==")[0] for p in packages ]
        return packages

    def pip3_package_is_installed(self, package):
        return package in self.get_installed_pip3_packages(with_versions=("==" in package))

    def install_pip3_package(self, package, force=False):
        assert type(package) is str
        if self.pip3_package_is_installed(package) and not force:
            print(package, "already installed.")
        else:
            self.sudo("pip3 install {p}".format(p=package))

    def install_pip3_packages(self, packages, force=False):
        assert type(packages) is list
        for package in packages:
            self.install_pip3_package(package, force)

    def uninstall_pip3_package(self, package):
        assert type(package) is str
        self.sudo("pip3 uninstall -y {p}".format(p=package))

    def uninstall_pip3_packages(self, packages):
        assert type(packages) is list
        for package in packages:
            self.uninstall_pip3_package(package)

# test

_server = None

def get_current_server():
    global _server
    host = "3.142.150.181"
    _server = _server or Server(host,"ubuntu","/home/runner/.ssh/lightsail-ohio.pem")
    return _server

def test_instantiate_server():
    server = get_current_server()
    assert type(server) is Server

def test_run():
    server = get_current_server()
    stdout, stderr = server.run("whoami")
    assert "ubuntu\n" == stdout
    assert "" == stderr
    stdout, stderr = server.run("whoami 1>&2")
    assert "" == stdout
    assert "ubuntu\n" == stderr

def test_sudo():
    server = get_current_server()
    stdout, stderr = server.sudo("whoami")
    assert "root\n" == stdout
    assert "" == stderr
    stdout, stderr = server.sudo("whoami 1>&2")
    assert "" == stdout
    assert "root\n" == stderr

def test_get_operating_system():
    server = get_current_server()
    name = server.get_operating_system()
    assert name == "Linux"

def test_update_apt_packages():
    server = get_current_server()
    server.update_apt_packages()

def test_get_installed_apt_packages():
    server = get_current_server()
    packages = server.get_installed_apt_packages()
    assert "nano" in packages
    assert "this-is-a-fake-package-name" not in packages

def test_apt_package_is_installed():
    server = get_current_server()
    assert server.apt_package_is_installed("nano") == True
    assert server.apt_package_is_installed("this-is-a-fake-package-name") == False

def test_install_apt_package():
    server = get_current_server()
    server.install_apt_package("python3-pip")
    assert server.apt_package_is_installed("python3-pip")

def test_install_apt_packages():
    server = get_current_server()
    server.install_apt_packages(["python3-pip", "nano"])
    assert server.apt_package_is_installed("python3-pip")

def test_get_running_processes():
    server = get_current_server()
    processes = server.get_running_processes()
    assert any([process for process in processes if '/usr/sbin/cron -f' in process])
    assert not any([process for process in processes if "this-is-a-fake-process-name" in process])

def test_process_is_running():
    server = get_current_server()
    assert server.process_is_running('/sbin/init')
    assert not server.process_is_running('/bin/vi')

def test_get_running_process_id():
    server = get_current_server()
    assert server.get_running_process_id('/sbin/init') == 1
    assert type(server.get_running_process_id('/usr/sbin/cron -f')) is int
    assert server.get_running_process_id('/bin/vi') == 0

# def test_kill_running_process():
#     server = get_current_server()
#     #assert server.get_running_process_id('/sbin/init') == 1
#     #assert type(server.get_running_process_id('/usr/sbin/cron -f')) is int
#     #assert server.get_running_process_id('/bin/vi') == 0

def test_python3_version():
    server = get_current_server()
    version = server.get_python3_version()
    assert version.startswith("3.8")

def test_pip3_version():
    server = get_current_server()
    version = server.get_pip3_version()
    assert version.startswith("20.0")
    assert "/3.8" in version

def test_get_git_version():
    server = get_current_server()
    version = server.get_git_version()
    assert version.startswith("2.")

def test_get_installed_pip3_packages():
    server = get_current_server()
    packages = server.get_installed_pip3_packages()
    assert type(packages) is list
    assert "pip" in packages
    version = server.get_pip3_version()
    version = version.split("/")[0]
    packages = server.get_installed_pip3_packages(with_versions=True)
    assert type(packages) is list
    assert "pip==" + version in packages

def test_pip3_package_is_installed():
    server = get_current_server()
    assert server.pip3_package_is_installed("pip")
    assert not (server.pip3_package_is_installed("fake-package-name"))
    version = server.get_pip3_version()
    version = version.split("/")[0]
    assert server.pip3_package_is_installed("pip==" + version)
    assert not (server.pip3_package_is_installed("pip==" + "1.2.3"))

def test_install_pip3_package():
    server = get_current_server()
    server.install_pip3_package("bottle")
    assert server.pip3_package_is_installed("bottle")

def test_uninstall_pip3_package():
    server = get_current_server()
    server.install_pip3_package("bottle")
    assert server.pip3_package_is_installed("bottle")
    server.uninstall_pip3_package("bottle")
    assert not server.pip3_package_is_installed("bottle")

def test_uninstall_pip3_packages():
    server = get_current_server()
    server.install_pip3_package("bottle")
    assert server.pip3_package_is_installed("bottle")
    server.uninstall_pip3_packages(["bottle"])
    assert not server.pip3_package_is_installed("bottle")

def test_put_get():
    server = get_current_server()
    server.run("ls -la", hide=False)
    server.put("server.py","temp123")
    server.run("ls -la", hide=False)
    server.get("temp123","temp456")

# main
if __name__ == "__main__":
    test_instantiate_server(); print("pass.")
    test_run(); print("pass.")
    test_sudo(); print("pass.")
    test_get_operating_system(); print("pass.")
    test_update_apt_packages(); print("pass.")
    test_get_installed_apt_packages(); print("pass.")
    test_apt_package_is_installed(); print("pass.")
    test_install_apt_package(); print("pass.")
    test_install_apt_packages(); print("pass.")
    test_get_running_processes(); print("pass.")
    test_process_is_running(); print("pass.")
    test_get_running_process_id(); print("pass.")
    test_python3_version(); print("pass.")
    test_pip3_version(); print("pass.")
    test_get_git_version(); print("pass.")
    test_get_installed_pip3_packages(); print("pass.")
    test_pip3_package_is_installed(); print("pass.")
    test_install_pip3_package(); print("pass.")
    test_uninstall_pip3_package(); print("pass.")
    test_uninstall_pip3_packages(); print("pass.")

    print("done.")
