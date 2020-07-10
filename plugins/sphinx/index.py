# coding:utf-8

import sys
import io
import os
import time
import re
import string
import subprocess

sys.path.append(os.getcwd() + "/class/core")
import mw

app_debug = False
if mw.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'sphinx'


def getPluginDir():
    return mw.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return mw.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def getConfTpl():
    path = getPluginDir() + "/conf/sphinx.conf"
    return path


def getConf():
    path = getServerDir() + "/sphinx.conf"
    return path


def getInitDTpl():
    path = getPluginDir() + "/init.d/" + getPluginName() + ".tpl"
    return path


def getArgs():
    args = sys.argv[2:]
    tmp = {}
    args_len = len(args)

    if args_len == 1:
        t = args[0].strip('{').strip('}')
        t = t.split(':')
        tmp[t[0]] = t[1]
    elif args_len > 1:
        for i in range(len(args)):
            t = args[i].split(':')
            tmp[t[0]] = t[1]
    return tmp


def checkArgs(data, ck=[]):
    for i in range(len(ck)):
        if not ck[i] in data:
            return (False, mw.returnJson(False, '参数:(' + ck[i] + ')没有!'))
    return (True, mw.returnJson(True, 'ok'))


def configTpl():
    path = getPluginDir() + '/tpl'
    pathFile = os.listdir(path)
    tmp = []
    for one in pathFile:
        file = path + '/' + one
        tmp.append(file)
    return mw.getJson(tmp)


def readConfigTpl():
    args = getArgs()
    data = checkArgs(args, ['file'])
    if not data[0]:
        return data[1]

    content = mw.readFile(args['file'])
    content = contentReplace(content)
    return mw.returnJson(True, 'ok', content)


def contentReplace(content):
    service_path = mw.getServerDir()
    content = content.replace('{$ROOT_PATH}', mw.getRootDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    content = content.replace('{$SERVER_APP}', service_path + '/sphinx')
    return content


def status():
    data = mw.execShell(
        "ps -ef|grep sphinx |grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] == '':
        return 'stop'
    return 'start'


def mkdirAll():
    content = mw.readFile(getConf())
    rep = 'path\s*=\s*(.*)'
    p = re.compile(rep)
    tmp = p.findall(content)

    for x in tmp:
        if x.find('binlog') != -1:
            mw.execShell('mkdir -p ' + x)
        else:
            mw.execShell('mkdir -p ' + os.path.dirname(x))


def initDreplace():

    file_tpl = getInitDTpl()
    service_path = os.path.dirname(os.getcwd())

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)
    file_bin = initD_path + '/' + getPluginName()

    # initd replace
    if not os.path.exists(file_bin):
        content = mw.readFile(file_tpl)
        content = contentReplace(content)
        mw.writeFile(file_bin, content)
        mw.execShell('chmod +x ' + file_bin)

    # config replace
    conf_bin = getConf()
    if not os.path.exists(conf_bin):
        conf_content = mw.readFile(getConfTpl())
        conf_content = contentReplace(conf_content)
        mw.writeFile(getServerDir() + '/sphinx.conf', conf_content)

    mkdirAll()
    return file_bin


def checkIndexSph():
    content = mw.readFile(getConf())
    rep = 'path\s*=\s*(.*)'
    p = re.compile(rep)
    tmp = p.findall(content)
    for x in tmp:
        if x.find('binlog') != -1:
            continue
        else:
            p = x + '.sph'
            if os.path.exists(p):
                return False
    return True


def start():
    file = initDreplace()

    data = sphinxConfParse()
    if 'index' in data:
        if checkIndexSph():
            rebuild()
            time.sleep(5)
    else:
        return '配置不正确!'

    data = mw.execShell(file + ' start')
    if data[1] == '':
        return 'ok'
    return data[1]


def stop():
    file = initDreplace()
    data = mw.execShell(file + ' stop')
    if data[1] == '':
        return 'ok'
    return data[1]


def restart():
    file = initDreplace()
    data = mw.execShell(file + ' restart')
    if data[1] == '':
        return 'ok'
    return data[1]


def reload():
    file = initDreplace()
    data = mw.execShell(file + ' reload')
    if data[1] == '':
        return 'ok'
    return 'fail'


def rebuild():
    file = initDreplace()
    subprocess.Popen(file + ' rebuild &',
                     stdout=subprocess.PIPE, shell=True)
    # data = mw.execShell(file + ' rebuild')
    return 'ok'


def initdStatus():
    if not app_debug:
        if mw.isAppleSystem():
            return "Apple Computer does not support"
    initd_bin = getInitDFile()
    if os.path.exists(initd_bin):
        return 'ok'
    return 'fail'


def initdInstall():
    import shutil
    if not app_debug:
        if mw.isAppleSystem():
            return "Apple Computer does not support"

    source_bin = initDreplace()
    initd_bin = getInitDFile()
    shutil.copyfile(source_bin, initd_bin)
    mw.execShell('chmod +x ' + initd_bin)
    mw.execShell('chkconfig --add ' + getPluginName())
    return 'ok'


def initdUinstall():
    if not app_debug:
        if mw.isAppleSystem():
            return "Apple Computer does not support"
    initd_bin = getInitDFile()
    os.remove(initd_bin)
    mw.execShell('chkconfig --del ' + getPluginName())
    return 'ok'


def runLog():
    path = getConf()
    content = mw.readFile(path)
    rep = 'log\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0]


def getPort():
    path = getConf()
    content = mw.readFile(path)
    rep = 'listen\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0]


def queryLog():
    path = getConf()
    content = mw.readFile(path)
    rep = 'query_log\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0]


def runStatus():
    s = status()
    if s != 'start':
        return mw.returnJson(False, '没有启动程序')

    sys.path.append(getPluginDir() + "/class")
    import sphinxapi

    sh = sphinxapi.SphinxClient()
    port = getPort()
    sh.SetServer('127.0.0.1', port)
    info_status = sh.Status()

    rData = {}
    for x in range(len(info_status)):
        rData[info_status[x][0]] = info_status[x][1]

    return mw.returnJson(True, 'ok', rData)


def sphinxConfParse():
    file = getConf()
    bin_dir = getServerDir()
    content = mw.readFile(file)
    rep = 'index\s(.*)'
    sindex = re.findall(rep, content)
    indexlen = len(sindex)
    cmd = {}
    if indexlen > 0:
        cmd_index = []
        cmd_delta = []
        for x in range(indexlen):
            if string.find(sindex[x], ':') != -1:
                cmd_delta.append(sindex[x])
            else:
                cmd_index.append(sindex[x])

        cmd['index'] = cmd_index
        cmd['delta'] = cmd_delta
        cmd['cmd'] = bin_dir + '/bin/bin/indexer -c ' + bin_dir + '/sphinx.conf'
    return cmd


def sphinxCmd():
    data = sphinxConfParse()
    if 'index' in data:
        return mw.returnJson(True, 'ok', data)
    else:
        return mw.returnJson(False, 'no index')


if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'status':
        print status()
    elif func == 'start':
        print start()
    elif func == 'stop':
        print stop()
    elif func == 'restart':
        print restart()
    elif func == 'reload':
        print reload()
    elif func == 'rebuild':
        print rebuild()
    elif func == 'initd_status':
        print initdStatus()
    elif func == 'initd_install':
        print initdInstall()
    elif func == 'initd_uninstall':
        print initdUinstall()
    elif func == 'conf':
        print getConf()
    elif func == 'config_tpl':
        print configTpl()
    elif func == 'read_config_tpl':
        print readConfigTpl()
    elif func == 'run_log':
        print runLog()
    elif func == 'query_log':
        print queryLog()
    elif func == 'run_status':
        print runStatus()
    elif func == 'sphinx_cmd':
        print sphinxCmd()
    else:
        print 'error'
