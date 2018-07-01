from subprocess import check_output


def shell(command):
    command_parts = [
        part
        for part in command.split(' ')
        if part.strip()
    ]
    return check_output(command_parts)

