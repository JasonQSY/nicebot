from slacker import Slacker
import psutil
import sys
import os
import re
import subprocess
import select
import socket
import datetime


def collect_gpu_info():
    MEMORY_FREE_RATIO = 0.05
    MEMORY_MODERATE_RATIO = 0.9
    GPU_FREE_RATIO = 0.05
    GPU_MODERATE_RATIO = 0.75

    # parse the command length argument
    command_length = 20
    color = True

    # for testing, the stdin can be provided in a file
    fake_stdin_path = os.getenv("FAKE_STDIN_PATH", None)
    stdin_lines = []
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        stdin_lines = sys.stdin.readlines()

    if fake_stdin_path is not None:
        with open(fake_stdin_path, 'rt') as f:
            lines = f.readlines()
    elif stdin_lines:
        lines = stdin_lines
    else:
        processes = subprocess.run('nvidia-smi', stdout=subprocess.PIPE)
        lines_proc = processes.stdout.decode().split("\n")
        lines = [line + '\n' for line in  lines_proc[:-1]]
        lines += lines_proc[-1]

    lines_to_print = []
    # Copy the utilization upper part verbatim
    for i in range(len(lines)):
        if not lines[i].startswith("| Processes:"):
            lines_to_print.append(lines[i].rstrip())
        else:
            i += 3
            break

    #for line in lines_to_print:
    #    print(line)

    # Parse the PIDs from the lower part
    gpu_num = []
    pid = []
    gpu_mem = []
    user = []
    cpu = []
    mem = []
    time = []
    command = []

    no_running_process = "No running processes found"
    if no_running_process in lines[i]:
        return gpu_num, pid, user, gpu_mem, cpu, mem, time, command

    while not lines[i].startswith("+--"):
        if "Not Supported" in lines[i]:
            i+=1
            continue
        line = lines[i]
        line = re.split(r'\s+', line)
        gpu_num.append(line[1])
        pid.append(line[2])
        gpu_mem.append(line[-3])
        user.append("")
        cpu.append("")
        mem.append("")
        time.append("")
        command.append("")
        i+=1

    # Query the PIDs using ps
    ps_format = "pid,user,%cpu,%mem,etime,command"
    processes = subprocess.run(["ps", "-o", ps_format, "-p", ",".join(pid)], stdout=subprocess.PIPE)

    # Parse ps output
    for line in processes.stdout.decode().split("\n"):
        if line.strip().startswith("PID") or len(line) == 0:
            continue
        parts = re.split(r'\s+', line.strip(), 5)
        idx = pid.index(parts[0])
        user[idx] = parts[1]
        cpu[idx] = parts[2]
        mem[idx] = parts[3]
        time[idx] = parts[4] if not "-" in parts[4] else parts[4].split("-")[0] + " days"
        command[idx] = parts[5][0:100]

    return gpu_num, pid, user, gpu_mem, cpu, mem, time, command


def collect_cpu_info():
    procs = psutil.process_iter(attrs=['pid', 'name', 'username','nice'])
    message = '```'
    cnt = 0
    for p in procs:
        info = p.info
        if 'python' not in info['name']:
            continue
        proc = psutil.Process(pid=info['pid'])
        nice = proc.nice()
        if nice < 10:
            message += str(info) + '\n'
            cnt += 1
    # Send a message to #general channel
    message += '```'


def main():
    # initialize nicebot
    #token = os.environ['NICEBOT_TOKEN']
    #slack = Slacker(token)
    message = ''
    now = '[time] ' + datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + '\n'

    # detect hostname and server-specific info
    hostname = socket.gethostname()
    prefix = now
    prefix += "Performing nice scan on {}: ".format(hostname)
    #if hostname == 'epicfail':
    #    prefix = ':fail: :epic: ' + prefix
    #elif hostname == 'titanic':
    #    prefix = ':iceberg:: ' + prefix

    # collect gpu info
    message += prefix + '\n'
    cnt = 0
    command_length = 50
    gpu_num, pid, user, gpu_mem, cpu, mem, time, command = collect_gpu_info()
    format = ("%3s %5s %4s %8s   %8s %5s %5s %9s  %-" + str(command_length) + "." + str(command_length) + "s")
    message += format % ("GPU", "PID", "NICE", "USER", "GPU MEM", "%CPU", "%MEM", "TIME", "COMMAND")
    message += '\n'
    for i in range(len(pid)):
        proc = psutil.Process(pid=int(pid[i]))
        nice = proc.nice()
        cnt += 1
        message += format % (gpu_num[i], pid[i], nice, user[i], gpu_mem[i],
            cpu[i], mem[i], time[i], command[i])
        message += '\n'
    #message += ''

    f = open('/Pool1/users/syqian/gpu_log/{}.log'.format(hostname), 'w')
    if cnt > 0:
        f.write(message)
        f.write('\n')
    else:
        f.write(prefix + "no job\n")

    f.close()


if __name__=='__main__':
    main()
