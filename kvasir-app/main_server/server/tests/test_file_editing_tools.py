from synesis_api.utils.code_utils import (
    add_lines_to_script_at_line,
    add_line_numbers_to_script,
    remove_line_numbers_from_script,
    replace_lines_in_script,
    delete_lines_from_script
)

script = """
Script: #!/bin/bash

# Setup script for TimeMixer repository

# Install dependencies
pip install einops==0.4.1 matplotlib==3.4.3 numpy==1.22.4 pandas==1.1.5 patool==1.12 reformer_pytorch==1.4.4 scikit_learn==1.2.1 scipy==1.8.0 sktime==0.29.1 torch==1.7.1 tqdm==4.64.0

# Note: If you are using Python 3.8, please ensure the correct version of sktime is set in requirements.

# Running the main script (make sure to set the correct parameters as needed)
python run.py --task_name long_term_forecast --is_training 1 --model_id test --model Autoformer --data ETTm1 --seq_len 96 --label_len 48 --pred_len 96
"""

new_code = """pip install einops==0.4.1 matplotlib==3.4.3 numpy==1.22.4 pandas==1.1.5 patool==1.12 reformer_pytorch==1.4.4 scikit_learn==1.2.1 scipy==1.8.0 sktime==0.29.1 torch==1.12.1 tqdm==4.64.0"""


if __name__ == "__main__":

    print("SCRIPT")
    print(script)
    print("@"*50)

    # Add line numbers to script
    script_with_line_numbers = add_line_numbers_to_script(script)
    print("SCRIPT WITH LINE NUMBERS")
    print(script_with_line_numbers)
    print("@"*50)

    # # Delete line numbers from script
    # script_without_line_numbers = remove_line_numbers_from_script(
    #     script_with_line_numbers)
    # print("SCRIPT WITHOUT LINE NUMBERS")
    # print(script_without_line_numbers)
    # print("@"*50)

    # Add lines to script
    new_script = add_lines_to_script_at_line(
        script_with_line_numbers,
        "# Comment for testing\n# Comment 2 for testing\n# Comment 3 for testing",
        start_line=21,
        script_has_line_numbers=True
    )

    # print("NEW SCRIPT AFTER ADDING LINES")
    # print(new_script)
    # print("@"*50)

    # # Delete lines from script
    # new_script = delete_lines_from_script(
    #     new_script,
    #     line_number_start=21,
    #     line_number_end=23,
    #     script_has_line_numbers=True
    # )

    # print("NEW SCRIPT AFTER DELETING LINES")
    # print(new_script)
    # print("@"*50)

    # Replace the line 10-12 with the new code
    new_script = replace_lines_in_script(
        script_with_line_numbers,
        line_number_start=6,
        line_number_end=8,
        new_code=new_code,
        script_has_line_numbers=True
    )
    print("NEW SCRIPT AFTER REPLACING LINES")
    print(new_script)
    print("@"*50)

    # # Deleting replaced lines
    # new_script = delete_lines_from_script(
    #     new_script,
    #     line_number_start=27,
    #     line_number_end=41,
    #     script_has_line_numbers=True
    # )
    # print("NEW SCRIPT AFTER DELETING REPLACED LINES")
    # print(new_script)
    # print("@"*50)
