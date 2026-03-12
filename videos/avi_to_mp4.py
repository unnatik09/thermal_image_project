import subprocess
import os


def convert_and_replace_avi(input_file):
    # Check if the file exists first
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Define the new filename
    output_file = os.path.splitext(input_file)[0] + ".mp4"

    # FFmpeg command
    command = [
        'ffmpeg',
        '-i', input_file,
        '-c:v', 'libx264',
        '-crf', '23',
        '-c:a', 'aac',
        '-y',  # Overwrite if mp4 exists
        output_file
    ]

    try:
        print(f"Converting {input_file}...")
        # run() will wait for the process to finish
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # Verify the new file exists and has size > 0 before deleting original
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            os.remove(input_file)
            print(f"Success! {input_file} has been replaced by {output_file}")
        else:
            print("Conversion failed: Output file is empty or missing.")

    except subprocess.CalledProcessError:
        print(f"FFmpeg crashed while processing {input_file}. Original file kept.")

# To run it on a specific file:
convert_and_replace_avi("TC001_20260312-131052.avi")