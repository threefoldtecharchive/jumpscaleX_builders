from Jumpscale import j


# TODO: *4 unfinished but ok for now


class BuilderHadoop(j.baseclasses.builder):
    def _install(self):

        if j.core.platformtype.myplatform.platform_is_ubuntu:
            C = """\
            apt-get install -y apt-get install openjdk-7-jre
            cd {DIR_TEMP}
            wget -c http://www-us.apache.org/dist/hadoop/common/hadoop-2.7.2/hadoop-2.7.2.tar.gz
            tar -xf hadoop-2.7.2.tar.gz -C /opt/
            """
            C = j.builders.tools.replace(C)
            C = self._replace(C)
            j.sal.process.execute(C, profile=True)
            # j.builders.sandbox.path_add("/opt/hadoop-2.7.2/bin")
            # j.builders.sandbox.path_add("/opt/hadoop-2.7.2/sbin")
            # j.builders.sandbox.env_set("JAVA_HOME", "/usr/lib/jvm/java-7-openjdk-amd64")
            # j.builders.sandbox.env_set("HADOOP_PREFIX", "/opt/hadoop-2.7.2/")
        else:
            raise j.exceptions.NotImplemented("unsupported platform")

    def install(self):
        self._install()
