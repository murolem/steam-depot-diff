def confirm(msg: str, default: bool = False):
    try:
        user_input = input(f'{msg} [{"Y/n" if default else "y/N"}]: ')
    except EOFError:
        return False

    if user_input == "":
        user_input = "y" if default else "n"

    # input validation
    if user_input.lower() in ('y', 'yes'):
        return True
    else:
        return False