import gradio as gr
import json
import subprocess

def scrape_unog(start_date, end_date, output_file, organization=None, meeting_type=None, keywords=None):
    # Build command
    cmd = ["./api_task.sh", "-s", start_date, "-e", end_date, "-o", output_file]
    
    # Add optional parameters if provided
    if organization:
        cmd.extend(["-g", organization])
    if meeting_type:
        cmd.extend(["-m", meeting_type]) 
    if keywords:
        cmd.extend(["-k", keywords])

    # Execute shell script
    try:
        subprocess.run(cmd, check=True)
        
        # Read results from output file
        results = []
        with open(output_file) as f:
            for line in f:
                results.append(json.loads(line))
                
        return results[:10], output_file
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Script execution failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error parsing output file: {str(e)}")
    except FileNotFoundError:
        raise RuntimeError(f"Output file {output_file} not found")

def download_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()

# Create Gradio interface with current API
iface = gr.Interface(
    fn=scrape_unog,
    inputs=[
        gr.Textbox(value="01/07/2024", label="Start Date (DD/MM/YYYY)"),
        gr.Textbox(value="01/08/2024", label="End Date (DD/MM/YYYY)"),
        gr.Textbox(value="meetings.jsonl", label="Output JSONL File"),
        gr.Textbox(value="UNHRC", label="Organization Code"),
        gr.Textbox(value="", label="Type of Meeting"),
        gr.Textbox(value="", label="Keywords for Filtering")
    ],
    outputs=[
        gr.JSON(label="JSONL Preview (First 10 Rows)"),
        gr.File(label="Download JSONL File")
    ],
    title="UNOG Digital Recordings Scraper",
    description="This tool scrapes the UNOG Digital Recordings page to extract all available meetings and creates a JSON Lines file with all the information.",
    allow_flagging=False
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0")