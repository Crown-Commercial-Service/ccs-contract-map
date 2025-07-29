
def file_to_string_processor(file_path):
    """ convert file to string

    :param file_path: string file path
    :return: string value
    """
    with open(file_path, "r", encoding='utf-8') as file:
        text_content = file.read()

    return text_content
