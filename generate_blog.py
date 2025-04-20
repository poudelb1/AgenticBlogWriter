import os
import logging
import json # Import json for parsing structured output
from crewai import Crew, Agent, Task # Import Task if needed for more complex flows
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
# *** IMPORTANT: CrewAI often integrates directly with specific LLM providers.
# Using "OpenAITextTool" might imply using OpenAI models.
# If you intend to use Google Gemini, you might need a different tool
# (e.g., a hypothetical `GoogleGeminiTool` or `VertexAITool` if available in CrewAI)
# or configure the agent's llm parameter directly if supported.
# We are ASSUMING usage of OpenAI-compatible models here based on the tool names.
from langchain_openai import ChatOpenAI, OpenAIEmbeddings # More explicit imports often needed
from langchain_community.tools import DuckDuckGoSearchRun # Example alternative search tool

# --- Tool Setup (Consider provider-specific tools) ---
# If using OpenAI:
from langchain_openai import OpenAI # If using OpenAI specific tools
# from crewai.tools import OpenAITextTool # If this wrapper works as intended for simple text
# from crewai.tools import OpenAIImageTool # Assumes DALL-E backend via OpenAI API

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

# --- Custom Exception ---
class BlogGenerationError(Exception):
    """Custom exception for errors during the blog generation pipeline."""
    pass
# ----------------------


def generate_blog(topic: str) -> dict:
    """
    Generates a blog post using a CrewAI pipeline.

    Args:
        topic: The subject for the blog article.

    Returns:
        A dictionary containing 'title', 'body_markdown', and 'image_url'.

    Raises:
        EnvironmentError: If required API keys are missing.
        BlogGenerationError: If any part of the CrewAI pipeline fails unexpectedly
                             or doesn't produce the expected output format.
    """
    logger.info(f"Starting blog generation process for topic: '{topic}'")

    # --- Load API Keys ---
    # Ensure necessary API keys are set in the environment (.env file)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    serper_api_key = os.getenv("SERPER_API_KEY")
    # duckduckgo_api_key = os.getenv("DUCKDUCKGO_API_KEY") # Example if using DDG

    if not openai_api_key:
        logger.error("Missing OPENAI_API_KEY in environment variables.")
        raise EnvironmentError("OpenAI API key not found in environment variables.")
    if not serper_api_key:
        # You might want to make Serper optional or use another search tool like DuckDuckGo
        logger.warning("Missing SERPER_API_KEY. Research capabilities might be limited.")
        # raise EnvironmentError("Serper API key not found.") # Or raise if required
        # Example fallback or alternative tool:
        search_tool = DuckDuckGoSearchRun()
    else:
        search_tool = SerperDevTool(api_key=serper_api_key)

    logger.info("API keys loaded successfully.")

    # --- Configure LLMs (Example using OpenAI) ---
    # It's often better to explicitly define the LLM for agents
    # Adjust model names as needed (e.g., "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo")
    default_llm = ChatOpenAI(
        model_name="gpt-4o-mini", # is cheaper and has higher Token Limits
        temperature=0.7, # Adjust creativity/factualness
        openai_api_key=openai_api_key
    )
    # image_llm = ... # If specific config needed for image generation model

    # --- Initialize Tools ---
    scrape_tool = ScrapeWebsiteTool()
    # text_tool = OpenAITextTool(llm=default_llm) # If using this specific wrapper
    # image_tool = OpenAIImageTool(api_key=openai_api_key) # Using the CrewAI wrapper
    # Ensure the image tool is instantiated (using crewai_tools if that worked for you)

    try:
        # Assuming you fixed the import to use crewai_tools
        from crewai_tools import DallETool
        image_tool = DallETool(model = 'dall-e-2',
                               size = '512x512',
                               api_key=openai_api_key) # Pass the key
    except ImportError:
        logger.error("Could not import OpenAIImageTool from crewai_tools. Image generation will likely fail.")
        image_tool = None # Set to None if import fails
    # --- Define Agents ---
    researcher = Agent(
        role='Senior Research Analyst',
        goal=f'Uncover the latest unbiased news, developments, and trends about "{topic}". Focus on factual information and key insights.',
        backstory=(
            "You are an expert research analyst known for your thoroughness and ability to synthesize "
            "complex information into concise, actionable reports. You prioritize credible sources."
        ),
        tools=[search_tool, scrape_tool],
        llm=default_llm,
        verbose=True, # Enable detailed logging for this agent
        allow_delegation=False
    )

    writer = Agent(
        role='Professional Content Writer',
        goal=f'Craft an engaging, well-structured, and informative blog post about "{topic}" based on the provided research report.',
        backstory=(
            "You are a skilled content writer specializing in technology and current events. You excel at transforming "
            "research findings into compelling narratives that resonate with a broad audience. You write in Markdown format."
        ),
        # tools=[text_tool], # Often agents don't need a dedicated text tool if they have an LLM
        llm=default_llm,
        verbose=True,
        allow_delegation=False
    )

    editor = Agent(
        role=' meticulous Editor',
        goal=(
            'Review the draft blog post for clarity, coherence, grammar, style, and accuracy. '
            'Improve the flow and ensure it is engaging. Format the final output as a JSON object '
            'containing two keys: "title" (string, a captivating title for the blog post) and '
            '"body" (string, the full refined blog post content in Markdown format).'
        ),
        backstory=(
            "You are a detail-oriented editor with a keen eye for compelling content. You ensure every piece "
            "is polished, professional, and ready for publication. You output structured data."
        ),
        # tools=[text_tool], # Editor primarily uses its LLM capabilities
        llm=default_llm,
        verbose=True,
        allow_delegation=False
    )

    # NOTE: Direct image generation within a standard text-based agent flow can be tricky.
    # The OpenAIImageTool might need specific prompting or handling.
    # Alternatively, image generation could be a separate step after text is finalized.
    image_generator = Agent(
         role='AI Image Generation Specialist',
         goal='Create a relevant and high-quality illustrative image for a blog post based on its title.',
         backstory=(
             "You are an AI specialized in interpreting text concepts (like blog titles) and generating "
             "visually appealing and relevant images using models like DALL-E. You return only the image URL."
         ),
         tools=[image_tool] if image_tool else [], # Assign the image tool
         llm=default_llm, # Image tool might use its own internal LLM/API call logic
         verbose=True,
         allow_delegation=False
     )

    # --- Define Tasks ---
    # Tasks structure the workflow and pass context between agents
    task_research = Task(
        description=f"Conduct comprehensive research on the latest news and trends about '{topic}'. Identify key facts, figures, and recent developments. Compile these into a detailed report.",
        expected_output="A comprehensive research report summarizing key findings about the topic, suitable for a content writer.",
        agent=researcher
    )

    task_write = Task(
        description=f"Write an engaging blog post about '{topic}' using the research report provided. Ensure the tone is informative yet accessible. Use Markdown format.",
        expected_output="A well-written draft of the blog post in Markdown format.",
        agent=writer
        # context=[task_research] # CrewAI automatically handles context passing in a Crew sequence
    )

    task_edit = Task(
        description=(
            "Review the draft blog post. Refine it for clarity, grammar, style, and flow. "
            "Extract a suitable title. Format the final output as a JSON object with 'title' and 'body' keys (body in Markdown)."
        ),
        expected_output=(
            'A JSON string containing the final blog post title and body. Example: '
            '{"title": "Example Title", "body": "# Introduction\\n\\nThis is the refined blog content..."}'
        ),
        agent=editor
        # context=[task_write]
    )

    # Image generation task - ensure the 'title' is available
    # This might require accessing the output of task_edit, which can be complex in a simple sequence.
    # Often, image generation is done *after* the text is fully finalized.
    # Let's try passing the topic for now, assuming the image agent can infer context,
    # or adjust the flow later if needed. A simpler approach might be to run this *after* getting the title.
    # task_image = Task(
    #     description=f"Generate a suitable illustrative image for a blog post titled about '{topic}'. The specific title will be provided later if possible.",
    #     expected_output="A URL string pointing to the generated image.",
    #     agent=image_generator
    #     # context might ideally include the title from task_edit
    # )

    # --- Create and Run the Crew ---
    blog_crew = Crew(
        agents=[researcher, writer, editor], # Image agent run separately for now
        tasks=[task_research, task_write, task_edit],
        verbose=True # Set verbosity level (0, 1, or 2)
    )

    logger.info("Starting CrewAI kickoff...")
    try:
        # Kick off the crew for text generation and editing
        crew_result = blog_crew.kickoff()
        logger.info("CrewAI process completed.")
        logger.debug(f"Raw CrewAI result: {crew_result}") # Log raw output for debugging

        # --- Process Edited Result (Expected JSON) ---
        final_title = f"Blog on {topic}" # Default title
        final_body = "Error: Could not parse editor output." # Default body

        try:
                raw_output_string = crew_result.raw  # Get the raw string output from the crew run
                logger.debug(f"Raw output string from editor task: {raw_output_string}")

                # Find the starting '{' of the JSON object
                json_start_index = raw_output_string.find('{')
                # Find the last '}' of the JSON object
                json_end_index = raw_output_string.rfind('}')

                if json_start_index != -1 and json_end_index != -1 and json_end_index > json_start_index:
                    # Extract the JSON part
                    json_string = raw_output_string[json_start_index : json_end_index + 1]
                    logger.debug(f"Attempting to parse extracted JSON: {json_string}")

                    # Parse the extracted JSON string
                    edited_output = json.loads(json_string)

                    # Extract title and body, keeping defaults if keys are missing in the JSON
                    parsed_title = edited_output.get("title")
                    parsed_body = edited_output.get("body")

                    if parsed_title:
                        final_title = parsed_title
                        logger.info(f"Successfully parsed title: '{final_title}'")
                    else:
                        logger.warning("Could not find 'title' key in parsed JSON.")
                        # Keep default final_title

                    if parsed_body:
                        final_body = parsed_body
                        logger.info("Successfully parsed body from JSON.")
                    else:
                        logger.warning("Could not find 'body' key in parsed JSON.")
                        # Keep default final_body (which is the error message)

                else:
                    # Log an error if no valid JSON structure '{...}' is found
                    logger.error(f"Could not find valid JSON structure '{{...}}' in raw output. Raw output: {raw_output_string}")
                    # Keep default final_title and final_body (error message)

        except (json.JSONDecodeError, TypeError, AttributeError, Exception) as parse_err:
            # Catch potential errors during string processing or JSON parsing
            logger.error(f"Failed during JSON parsing/extraction: {parse_err}. Raw output: {crew_result.raw if hasattr(crew_result, 'raw') else crew_result}", exc_info=True)
            # Keep default final_title and final_body (error message)

        # --- Generate Image (Run separately after getting title) ---
        image_url = None
        if final_title != f"Blog on {topic}": # Only if a real title was parsed
            logger.info(f"Generating image for title: '{final_title}'")
            try:
                # Define and run the image task dynamically
                task_image = Task(
                    description=f"Generate a suitable illustrative image for a blog post titled '{final_title}'.",
                    expected_output="A URL string pointing to the generated image, or an empty string/null if failed.",
                    agent=image_generator
                )
                # Create a temporary crew or run the task directly if CrewAI allows
                # Running task directly (syntax might vary based on CrewAI version):
                # image_result = task_image.execute()
                # OR using a minimal crew:
                image_crew = Crew(agents=[image_generator], tasks=[task_image], verbose=True)
                image_result = image_crew.kickoff()

                # Assuming image_result is the URL string directly or parse if needed
                # if isinstance(image_result, str) and image_result.startswith("http"):
                #     image_url = image_result
                #     logger.info(f"Image generated successfully: {image_url}")
                # else:
                #     logger.warning(f"Image generation did not return a valid URL. Result: {image_result}")

                if hasattr(image_result, "raw"):
                    raw_out = image_result.raw
                elif isinstance(image_result, (list, tuple)) and hasattr(image_result[0], "raw"):
                    raw_out = image_result[0].raw
                else:
                    raw_out = str(image_result)

                # Strip quotes/whitespace
                img_url_candidate = raw_out.strip().strip('"').strip("'")
                if img_url_candidate.startswith("http"):
                    image_url = img_url_candidate
                    logger.info(f"Image generated successfully: {image_url}")
                else:
                    logger.warning("Invalid image URL from image agent: %r", raw_out)

            except Exception as img_err:
                 logger.error(f"Failed during image generation task: {img_err}", exc_info=True)
                 # Keep image_url as None
        else:
            logger.warning("Skipping image generation due to fallback title.")


    except Exception as e:
        logger.error(f"Error during CrewAI kickoff or result processing: {e}", exc_info=True)
        raise BlogGenerationError(f"CrewAI pipeline failed: {e}") from e

    # --- Return Final Dictionary ---
    # Ensure keys match the BlogResponse model in app.py
    final_result = {
        "title": final_title,
        "body_markdown": final_body,
        "image_url": image_url
    }
    logger.info(f"-------> Returning final result dictionary: {json.dumps(final_result, indent=2)}")
    return final_result

# --- Command-Line Execution (for testing) ---
if __name__ == "__main__":
    import argparse

    # Ensure environment variables are loaded if run directly
    from dotenv import load_dotenv
    load_dotenv()

    # Basic logging for direct script execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Generate a blog post using CrewAI.")
    parser.add_argument("--topic", type=str, required=True, help="Topic for the blog article.")
    args = parser.parse_args()

    try:
        result = generate_blog(args.topic)
        print("\n--- Generated Blog Post ---")
        print(f"Title: {result['title']}\n")
        print("--- Body (Markdown) ---")
        print(result['body_markdown'])
        print("\n--- Image ---")
        print(f"Image URL: {result['image_url']}")
        print("\n---------------------------\n")
    except (EnvironmentError, BlogGenerationError, Exception) as e:
        print(f"\n--- ERROR ---")
        print(f"An error occurred: {e}")
        print("----------------\n")