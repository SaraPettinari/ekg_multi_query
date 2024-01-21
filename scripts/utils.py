import pandas as pd
import scripts.queries as queries
import scripts.constants as cn


def set_entity_data(path, log_name):
    """
    Given a list, puts the predefined value in the last position.

    Parameters:
    - path: path of the file.
    - log_name: entity log name.

    Returns:
    - query: the query to be executed.
    - columns: entity file header.
    """
    out_data = {cn.PATH : path, cn.LOGNAME: log_name}
    df = pd.read_csv(path)
    column_names = list(df.columns)
    for col in column_names:
        out_data[col] = col

    load_query = queries.load_generator(out_data, node_type=cn.ENTITY)
    
    return {'query': load_query, 'columns': column_names}



def put_value_in_last_position(input_list : list, value):
    """
    Given a list, puts the predefined value in the last position.

    Parameters:
    - input_list (list): The input list.
    - value: The value to be placed in the last position.

    Returns:
    - list: The modified list.
    """
    # Remove the predefined value from the list, if it already exists
    if value in input_list:
        input_list.remove(value)

    # Append the predefined value to the end of the list
    input_list.append(value)

    return input_list
