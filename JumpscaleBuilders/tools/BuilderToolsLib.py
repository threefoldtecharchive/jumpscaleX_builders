import base64

NOTHING = base64

STRINGIFY_MAXSTRING = 80
STRINGIFY_MAXLISTSTRING = 20


# MODE_LOCAL              = "MODE_LOCAL"
# MODE_SUDO               = "MODE_SUDO"

# SUDO_PASSWORD           = "CUISINE_SUDO_PASSWORD"
# OPTION_PACKAGE          = "CUISINE_OPTION_PACKAGE"
# OPTION_PYTHON_PACKAGE   = "CUISINE_OPTION_PYTHON_PACKAGE"
# OPTION_OS_FLAVOUR       = "CUISINE_OPTION_OS_FLAVOUR"
# OPTION_USER             = "CUISINE_OPTION_USER"
# OPTION_GROUP            = "CUISINE_OPTION_GROUP"
# OPTION_HASH             = "CUISINE_OPTION_HASH"


def stringify(value):
    """Turns the given value in a user-friendly string that can be displayed"""
    if isinstance(value, (str, bytes)) and len(value) > STRINGIFY_MAXSTRING:
        return "{0}...".format(value[0:STRINGIFY_MAXSTRING])

    if isinstance(value, (list, tuple)) and len(value) > 10:
        return "[{0},...]".format(", ".join([stringify(_) for _ in value[0:STRINGIFY_MAXLISTSTRING]]))
    return str(value)


def text_detect_eol(text):
    MAC_EOL = "\n"
    UNIX_EOL = "\n"
    WINDOWS_EOL = "\r\n"

    # TODO: Should look at the first line
    if text.find("\r\n") != -1:
        return WINDOWS_EOL
    if text.find("\n") != -1:
        return UNIX_EOL
    if text.find("\r") != -1:
        return MAC_EOL
    return "\n"


def text_get_line(text, predicate):
    """Returns the first line that matches the given predicate."""
    for line in text.split("\n"):
        if predicate(line):
            return line
    return ""


def text_normalize(text):
    """Converts tabs and spaces to single space and strips the text."""
    RE_SPACES = re.compile("[\s\t]+")
    return RE_SPACES.sub(" ", text).strip()


def text_nospace(text):
    """Converts tabs and spaces to single space and strips the text."""
    RE_SPACES = re.compile("[\s\t]+")
    return RE_SPACES.sub("", text).strip()


def text_replace_line(text, old, new, find=lambda old, new: old == new, process=lambda _: _):
    """Replaces lines equal to 'old' with 'new', returning the new
    text and the count of replacements.

    Returns: (text, number of lines replaced)

    `process` is a function that will pre-process each line (you can think of
    it as a normalization function, by default it will return the string as-is),
    and `find` is the function that will compare the current line to the
    `old` line.

    The finds the line using `find(process(current_line), process(old_line))`,
    and if this matches, will insert the new line instead.
    """
    res = []
    replaced = 0
    eol = text_detect_eol(text)
    for line in text.split(eol):
        if find(process(line), process(old)):
            res.append(new)
            replaced += 1
        else:
            res.append(line)
    return eol.join(res), replaced


def text_replace_regex(text, regex, new, **kwargs):
    """Replace lines that match with the regex returning the new text

    Returns: text

    `kwargs` is for the compatibility with re.sub(),
    then we can use flags=re.IGNORECASE there for example.
    """
    res = []
    eol = text_detect_eol(text)
    for line in text.split(eol):
        res.append(re.sub(regex, new, line, **kwargs))
    return eol.join(res)


def text_ensure_line(text, *lines):
    """Ensures that the given lines are present in the given text,
    otherwise appends the lines that are not already in the text at
    the end of it."""
    eol = text_detect_eol(text)
    res = list(text.split(eol))
    if res[0] == "" and len(res) == 1:
        res = list()
    for line in lines:
        assert line.find(eol) == -1, "No EOL allowed in lines parameter: " + repr(line)
        found = False
        for l in res:
            if l == line:
                found = True
                break
        if not found:
            res.append(line)
    return eol.join(res)


def text_strip_margin(text, margin="|"):
    """Will strip all the characters before the left margin identified
    by the `margin` character in your text. For instance

    ```
            |Hello, world!
    ```

    will result in

    ```
    Hello, world!
    ```
    """
    res = []
    eol = text_detect_eol(text)
    for line in text.split(eol):
        l = line.split(margin, 1)
        if len(l) == 2:
            _, line = l
            res.append(line)
    return eol.join(res)


# def text_template(text, variables):
#     """Substitutes '${PLACEHOLDER}'s within the text with the
#     corresponding values from variables."""
#     template = string.Template(text)
#     return template.safe_substitute(variables)
