# Simplified AI Podcast Generator with Artwork Background
import os
import time
import io
import uuid
import logging
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import tempfile
import requests
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to parse script for different voices
def parse_script_for_voices(script):
    """Parse the script to separate lines by character"""
    script_segments = {
        "NARRATOR": [],
        "CHARACTER1": [],
        "CHARACTER2": [],
        "OTHER": []
    }
    
    current_character = "NARRATOR"
    lines = script.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for character name pattern (ALL CAPS followed by colon)
        if ":" in line and line.split(":")[0].isupper():
            character_name = line.split(":")[0].strip()
            dialog = ":".join(line.split(":")[1:]).strip()
            
            if "NARRATOR" in character_name:
                script_segments["NARRATOR"].append(dialog)
                current_character = "NARRATOR"
            elif character_name == script_segments.get("CHARACTER1_NAME", ""):
                script_segments["CHARACTER1"].append(dialog)
                current_character = "CHARACTER1"
            elif character_name == script_segments.get("CHARACTER2_NAME", ""):
                script_segments["CHARACTER2"].append(dialog)
                current_character = "CHARACTER2"
            else:
                if "CHARACTER1_NAME" not in script_segments:
                    script_segments["CHARACTER1_NAME"] = character_name
                    script_segments["CHARACTER1"].append(dialog)
                    current_character = "CHARACTER1"
                elif "CHARACTER2_NAME" not in script_segments:
                    script_segments["CHARACTER2_NAME"] = character_name
                    script_segments["CHARACTER2"].append(dialog)
                    current_character = "CHARACTER2"
                else:
                    script_segments["OTHER"].append(line)
                    current_character = "OTHER"
        else:
            # Continue with current character or treat as narration
            script_segments[current_character].append(line)
            
    return script_segments

# Generate placeholder artwork
def generate_placeholder_artwork(theme, style):
    """Generate a colored placeholder with text as artwork"""
    # Generate a colored rectangle with text
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Set background color based on style
    style_colors = {
        "Realistic": "#4e8df5",
        "Cartoon": "#f55e4e",
        "Minimalist": "#5ef54e",
        "Pixel Art": "#f54ec5",
        "Watercolor": "#4ef5e8",
        "Comic": "#f5a74e"
    }
    bg_color = style_colors.get(style, "#4e8df5")
    ax.set_facecolor(bg_color)
    
    # Add podcast title
    ax.text(0.5, 0.6, f"{theme}",
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=36, color='white',
            fontweight='bold',
            wrap=True)
    
    # Add style text
    ax.text(0.5, 0.4, f"({style} Style)",
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=24, color='white',
            fontstyle='italic')

    # Add decorative elements
    for i in range(10):
        x = np.random.rand()
        y = np.random.rand()
        size = np.random.rand() * 1000
        alpha = np.random.rand() * 0.3
        ax.scatter(x, y, s=size, alpha=alpha, color='white')
    
    ax.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', pad_inches=0, dpi=300)
    buf.seek(0)
    
    # Convert to PIL Image
    image = Image.open(buf)
    plt.close(fig)  # Close the figure to free memory
    return image

def generate_artwork(theme, style):
    """Generate podcast artwork using Stability AI"""
    try:
        # Use the Stability AI API to generate artwork
        stability_api_key = "sk-13bsukSh9OM3invyyv3EA8SG3foSBEVTTrjNrBBJaEphOJ3k"
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        # Map our styles to appropriate prompts
        style_prompts = {
            "Realistic": "photorealistic, high-quality, detailed",
            "Cartoon": "cartoon style, vibrant colors, fun, animated",
            "Minimalist": "minimalist design, clean, simple shapes, limited color palette",
            "Pixel Art": "8-bit style, pixel art, retro gaming aesthetic",
            "Watercolor": "watercolor painting, soft edges, artistic, flowing colors",
            "Comic": "comic book style, bold lines, vibrant colors, action-oriented"
        }
        
        style_prompt = style_prompts.get(style, "high-quality")
        
        # Create the prompt for the image
        prompt = f"A podcast cover art about '{theme}', {style_prompt}, professional design, suitable for audio content"
        
        # API request parameters
        headers = {
            "Authorization": f"Bearer {stability_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        st.info(f"Generating artwork with prompt: {prompt}")
        
        # Make the API request
        response = requests.post(url, headers=headers, json=payload) 
        
        if response.status_code != 200:
            st.error(f"Failed to generate image: {response.text}")
            return generate_placeholder_artwork(theme, style)
            
        # Process the response
        data = response.json()
        
        if "artifacts" in data and len(data["artifacts"]) > 0:
            # Get the base64 encoded image
            image_data = data["artifacts"][0]["base64"]
            
            # Convert base64 to image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            return image
        else:
            st.error("No image was generated")
            return generate_placeholder_artwork(theme, style)
            
    except Exception as e:
        logger.error(f"Exception in artwork generation: {str(e)}")
        st.error(f"Error generating artwork: {str(e)}")
        return generate_placeholder_artwork(theme, style)

def generate_voices_with_gtts(script, voices):
    """Generate voice audio using Google Text-to-Speech with improved error handling"""
    script_segments = parse_script_for_voices(script)
    audio_files = {}
    
    # Map our voice names to gTTS languages/accents
    voice_mapping = {
        "Morgan (Neutral)": {"lang": "en", "tld": "com"},
        "Sophie (Cheerful)": {"lang": "en", "tld": "co.uk"},
        "James (Deep)": {"lang": "en", "tld": "com"},
        "Aria (Soft)": {"lang": "en", "tld": "co.uk"},
        "Marcus (Energetic)": {"lang": "en", "tld": "com.au"},
        "Alex (Young)": {"lang": "en", "tld": "ca"},
        "Elena (Smooth)": {"lang": "en", "tld": "co.in"},
        "Omar (Accent)": {"lang": "en", "tld": "com.au"},
        "Lily (High)": {"lang": "en", "tld": "co.uk"},
        "David (Authoritative)": {"lang": "en", "tld": "com"},
        "Taylor (Quirky)": {"lang": "en", "tld": "ca"},
        "Noah (Calm)": {"lang": "en", "tld": "com"},
        "Zoe (Bubbly)": {"lang": "en", "tld": "co.uk"},
        "Victor (Gruff)": {"lang": "en", "tld": "com.au"},
        "Maya (Melodic)": {"lang": "en", "tld": "co.in"}
    }
    
    characters_to_process = {key: value for key, value in script_segments.items() 
                           if key not in ["CHARACTER1_NAME", "CHARACTER2_NAME"]}
    
    progress_placeholder = st.empty()
    progress_bar = st.progress(0)
    total_characters = len(characters_to_process)
    
    temp_dir = tempfile.mkdtemp()
    
    for i, (character, lines) in enumerate(characters_to_process.items()):
        if not lines:
            continue
            
        # Select voice
        if character == "NARRATOR":
            voice_params = voice_mapping.get(voices["narrator"], {"lang": "en", "tld": "com"})
        elif character == "CHARACTER1":
            voice_params = voice_mapping.get(voices["character1"], {"lang": "en", "tld": "co.uk"})
        elif character == "CHARACTER2": 
            voice_params = voice_mapping.get(voices["character2"], {"lang": "en", "tld": "com.au"})
        else:
            voice_params = voice_mapping.get("Morgan (Neutral)", {"lang": "en", "tld": "com"})
            
        text_content = "\n".join(lines[:10])
        
        progress_placeholder.text(f"Generating {character} voice...")
        progress_bar.progress((i + 1) / max(1, total_characters))
        
        # Try up to 3 times with different TLDs if one fails
        success = False
        alternate_tlds = ["com", "co.uk", "ca", "co.in", "com.au"]
        
        for attempt, tld in enumerate(alternate_tlds[:3]):
            try:
                # Create unique filename
                filename = f"{temp_dir}/{character}_{uuid.uuid4()}.mp3"
                
                # Override TLD if previous attempts failed
                if attempt > 0:
                    voice_params["tld"] = tld
                    
                # Generate speech with timeout
                tts = gTTS(text=text_content, lang=voice_params["lang"], tld=voice_params["tld"], slow=False)
                tts.save(filename)
                
                audio_files[character] = filename
                st.success(f"Generated audio for {character}")
                success = True
                break
                    
            except Exception as e:
                st.warning(f"Attempt {attempt+1} failed for {character}: {str(e)}")
                time.sleep(1)  # Wait before retrying
        
        if not success:
            st.error(f"All attempts failed for {character}")
            # Create a fallback silent audio file
            try:
                filename = f"{temp_dir}/{character}_fallback.mp3"
                # Create a 1-second silent MP3 as fallback
                with open(filename, 'wb') as f:
                    f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                audio_files[character] = filename
                st.warning(f"Using silent fallback for {character}")
            except:
                audio_files[character] = None
    
    progress_placeholder.empty()
    progress_bar.empty()
    
    if not any(audio_files.values()):
        st.error("Could not generate any voice audio. Check your internet connection.")
    
    return {"status": "complete", "audio_files": audio_files}

# Function to generate script with placeholder
def generate_script(theme, language, age_group, tone, length):
    """Generate podcast script using placeholder implementation"""
    
    # Create a placeholder script
    placeholder_script = f"""NARRATOR: Welcome to our podcast about {theme}! Today we'll explore this fascinating topic with our guests.

CHARACTER1: Hi everyone! I'm so excited to be here talking about {theme}.

CHARACTER2: Yes, this is going to be a great discussion. I've been researching {theme} for years.

NARRATOR: Let's start by understanding what {theme} really means.

CHARACTER1: Well, in my experience, {theme} is all about discovery and imagination.

CHARACTER2: That's one perspective, but I think there's more to it. {theme} also involves critical thinking and analysis.

NARRATOR: Both excellent points! Let's dive deeper into how {theme} impacts our daily lives...

CHARACTER1: I remember when I first encountered {theme}, it completely changed my outlook.

CHARACTER2: Interesting! My journey was quite different. I initially dismissed {theme} until I saw its practical applications.

NARRATOR: These personal experiences really highlight the diverse ways people connect with {theme}.

CHARACTER1: Absolutely! And I think that's what makes {theme} so universal.

CHARACTER2: I agree. Despite our different approaches, we both value what {theme} brings to society.

NARRATOR: As we wrap up today's discussion, remember that {theme} continues to evolve and shape our world in unexpected ways.

CHARACTER1: It's been a pleasure sharing my thoughts with everyone today.

CHARACTER2: Likewise! I hope our listeners feel inspired to explore {theme} further.

NARRATOR: Thanks for listening to our podcast. Join us next time for another fascinating discussion!"""
    
    return placeholder_script

# Function to generate show notes with placeholder
def generate_show_notes(script):
    """Generate podcast show notes using placeholder implementation"""
    try:
        # Parse the script and generate placeholder notes
        lines = script.split('\n')
        title = "Exploring New Frontiers"
        summary = "In this episode, our hosts dive deep into fascinating topics with expert guests."
        
        # Extract bullet points from script
        bullet_points = []
        for line in lines[:10]:  # Just use first few lines for demo
            if ":" in line and not line.startswith("NARRATOR"):
                character = line.split(":")[0].strip()
                point = ":".join(line.split(":")[1:]).strip()
                if len(point) > 20:  # Only include substantial points
                    bullet_points.append(f"- {character} discusses {point[:50]}...\n")
        
        # Generate placeholder show notes
        show_notes = f"""# {title}

## Episode Summary
{summary}

## Key Points
{"".join(bullet_points[:5])}

## Resources Mentioned
- Resource 1: Example link
- Resource 2: Example link

## Timestamps
00:00 - Introduction
03:45 - Main discussion begins
08:30 - Key insights
15:20 - Conclusion

## Connect With Us
Website: podgenie.example.com
Twitter: @PodGenie
Instagram: @PodGenieOfficial
"""
        return show_notes
        
    except Exception as e:
        logger.error(f"Exception in show notes generation: {str(e)}")
        return f"Error generating show notes: {str(e)}"

# Function to save podcast
def save_podcast(podcast_data):
    """Save podcast data to database or file system"""
    try:
        # Generate a unique ID for the podcast
        podcast_id = f"pod_{int(time.time())}"
        
        # In a real implementation, we would save to database or file system
        logger.info(f"Saving podcast {podcast_id}: {podcast_data['theme']}")
        
        # Return the podcast ID
        return podcast_id
        
    except Exception as e:
        logger.error(f"Exception in saving podcast: {str(e)}")
        return None

def create_simple_video(artwork_path, audio_path):
    """Create a simple video by displaying artwork over audio"""
    try:
        from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
        
        # Generate unique video filename
        video_path = f"temp_video_{uuid.uuid4()}.mp4"
        
        # Load the image and audio
        image_clip = ImageClip(artwork_path).set_duration(10)  # Set image duration
        audio_clip = AudioFileClip(audio_path)
        
        # Set the image duration to match the audio duration
        image_clip = image_clip.set_duration(audio_clip.duration)
        
        # Set the audio of the clip
        video_clip = image_clip.set_audio(audio_clip)
        
        # Write the result to a file
        video_clip.write_videofile(video_path, fps=24)
        
        # Return the paths to use in the UI
        return {
            "audio_path": audio_path,
            "artwork_path": artwork_path,
            "video_path": video_path,
            "status": "complete"
        }
    except ImportError:
        st.error("Missing moviepy library. Install with: pip install moviepy")
        return {
            "audio_path": audio_path,
            "artwork_path": artwork_path,
            "video_path": None,
            "status": "error",
            "error": "Missing required library: moviepy"
        }
    except Exception as e:
        st.error(f"Error creating video: {str(e)}")
        return {
            "audio_path": audio_path,
            "artwork_path": artwork_path,
            "video_path": None,
            "status": "error",
            "error": str(e)
        }

# Assemble the final podcast audio
def assemble_podcast(voice_data, script):
    """Assemble the final podcast audio from voice data by combining all character tracks"""
    progress_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    try:
        from pydub import AudioSegment
        import os
        
        progress_placeholder.text("Step 1: Loading audio files...")
        progress_bar.progress(0.2)
        
        # Get audio files from voice data
        audio_files = voice_data.get("audio_files", {})
        if not audio_files:
            raise Exception("No audio files available to assemble")
        
        # Parse script to get proper ordering of lines
        progress_placeholder.text("Step 2: Analyzing script for audio ordering...")
        progress_bar.progress(0.4)
        
        script_lines = script.split('\n')
        ordered_segments = []
        
        # Create ordered list of which character speaks when
        for line in script_lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for character prefix pattern
            if ":" in line:
                parts = line.split(":", 1)
                character = parts[0].strip()
                
                # Map characters to our audio file keys
                if "NARRATOR" in character:
                    character_key = "NARRATOR"
                elif character == voice_data.get("CHARACTER1_NAME", "CHARACTER1"):
                    character_key = "CHARACTER1"
                elif character == voice_data.get("CHARACTER2_NAME", "CHARACTER2"):
                    character_key = "CHARACTER2"
                else:
                    character_key = "OTHER"
                
                # Add to ordered segments if we have audio for this character
                if character_key in audio_files and audio_files[character_key]:
                    ordered_segments.append(character_key)
        
        progress_placeholder.text("Step 3: Combining audio tracks...")
        progress_bar.progress(0.6)
        
        # Initialize with the first audio file or empty audio
        if ordered_segments and audio_files.get(ordered_segments[0]):
            combined_audio = AudioSegment.from_file(audio_files[ordered_segments[0]], format="mp3")
        else:
            # Create a silent audio segment as fallback
            combined_audio = AudioSegment.silent(duration=1000)
        
        # Add short pause between segments
        pause = AudioSegment.silent(duration=500)  # 500ms pause
        
        # Combine all audio files in order with pauses
        processed_keys = {ordered_segments[0]} if ordered_segments else set()
        
        for i, character_key in enumerate(ordered_segments[1:], start=1):
            # Skip if we've already processed this character (avoid duplicates)
            if character_key in processed_keys:
                continue
                
            processed_keys.add(character_key)
            
            try:
                # Load audio file
                if audio_files.get(character_key):
                    segment_audio = AudioSegment.from_file(audio_files[character_key], format="mp3")
                    
                    # Add pause between segments
                    combined_audio += pause + segment_audio
                    
                    # Update progress
                    progress_bar.progress(0.6 + (0.3 * i / max(1, len(ordered_segments))))
            except Exception as e:
                st.warning(f"Could not process audio for {character_key}: {str(e)}")
        
        progress_placeholder.text("Step 4: Finalizing podcast audio...")
        progress_bar.progress(0.9)
        
        # Export the combined audio to a file
        output_filename = f"final_podcast_{uuid.uuid4()}.mp3"
        combined_audio.export(output_filename, format="mp3")
        
        # Calculate actual duration
        duration_seconds = len(combined_audio) / 1000
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration = f"{minutes}:{seconds:02d}"
        
        progress_placeholder.text("Complete!")
        progress_bar.progress(1.0)
        
        result = {
            "status": "complete",
            "audio_file": output_filename,
            "duration": duration
        }
        
    except ImportError:
        st.error("Missing pydub library. Install with: pip install pydub")
        result = {
            "status": "error",
            "audio_file": voice_data.get("audio_files", {}).get("NARRATOR"),
            "duration": "0:00",
            "error": "Missing required library: pydub"
        }
    except Exception as e:
        st.error(f"Error assembling podcast: {str(e)}")
        # Fallback to using just the narrator track
        final_audio = voice_data.get("audio_files", {}).get("NARRATOR")
        if not final_audio:
            # Try any available track
            for key, value in voice_data.get("audio_files", {}).items():
                if value:
                    final_audio = value
                    break
        
        result = {
            "status": "partial",
            "audio_file": final_audio,
            "duration": "N/A",
            "error": str(e)
        }
    
    # Clean up UI elements
    progress_placeholder.empty()
    progress_bar.empty()
    
    return result

# Updated main app functions to integrate the simplified components
def create_podcast_page():
    st.markdown("# Create New Podcast")
    
    # Initialize session state if needed
    if 'processing_step' not in st.session_state:
        st.session_state.processing_step = None
    if 'current_podcast' not in st.session_state:
        st.session_state.current_podcast = {}
    
    if st.session_state.processing_step is None:
        with st.form("create_podcast_form"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                theme = st.text_input("Podcast Theme or Topic", "Space adventure for curious kids")
                st.markdown("#### Podcast Settings")
                
                col1a, col1b = st.columns(2)
                with col1a:
                    language = st.selectbox("Language", ["English", "Spanish", "French", "German", "Mandarin", "Hindi", "Japanese"])
                    tone = st.selectbox("Tone", ["Funny", "Dramatic", "Informative", "Mysterious", "Educational", "Inspirational"])
                
                with col1b:
                    age_group = st.selectbox("Target Age Group", ["Children (0-12)", "Teenagers (13-18)", "Young Adults (19-30)", "Adults (31-45)", "Seniors (46+)"])
                    length = st.select_slider("Episode Length (minutes)", options=[5, 10, 15, 20, 30, 45, 60])
                
                st.markdown("#### Voice Selection")
                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1:
                    narrator_voice = st.selectbox("Narrator Voice", ["Morgan (Neutral)", "Sophie (Cheerful)", "James (Deep)", "Aria (Soft)", "Marcus (Energetic)"])
                with col_v2:
                    char1_voice = st.selectbox("Character 1 Voice", ["Alex (Young)", "Elena (Smooth)", "Omar (Accent)", "Lily (High)", "David (Authoritative)"])
                with col_v3:
                    char2_voice = st.selectbox("Character 2 Voice", ["Taylor (Quirky)", "Noah (Calm)", "Zoe (Bubbly)", "Victor (Gruff)", "Maya (Melodic)"])
                
                st.markdown("#### Video Options")
                include_video = st.checkbox("Generate video podcast with artwork background", True)
            
            with col2:
                st.markdown("#### Cover Art Style")
                art_style = st.selectbox("Artwork Style", ["Realistic", "Cartoon", "Minimalist", "Pixel Art", "Watercolor", "Comic"])
                
                st.markdown("#### AI-Generated Cover Art")
                preview_image = generate_placeholder_artwork(theme, art_style)
                st.image(preview_image, use_container_width=True, caption="Preview (Will be regenerated)")
                
                st.markdown("#### Publishing Options")
                auto_publish = st.checkbox("Auto-publish to platforms", False)
                generate_notes = st.checkbox("Generate show notes", True)
                
                st.markdown("#### Advanced")
                edit_script = st.checkbox("Edit generated script before production", False)
            
            submit_button = st.form_submit_button("Generate Podcast")
            
            if submit_button:
                # Start the podcast generation pipeline
                st.session_state.processing_step = "script"
                st.session_state.current_podcast = {
                    "theme": theme,
                    "language": language,
                    "age_group": age_group,
                    "tone": tone,
                    "length": length,
                    "voices": {
                        "narrator": narrator_voice,
                        "character1": char1_voice,
                        "character2": char2_voice
                    },
                    "include_video": include_video,
                    "art_style": art_style,
                    "auto_publish": auto_publish,
                    "generate_notes": generate_notes,
                    "edit_script": edit_script
                }
                
                # Rerun to show processing UI
                st.rerun()
    
    # Handle script generation
    elif st.session_state.processing_step == "script":
        st.markdown("### Step 1: Generating Script")
        podcast_data = st.session_state.current_podcast
        
        # Show spinner during script generation
        with st.spinner(f"Generating a {podcast_data['tone']} script about {podcast_data['theme']}..."):
            script = generate_script(
                podcast_data['theme'],
                podcast_data['language'],
                podcast_data['age_group'],
                podcast_data['tone'],
                podcast_data['length']
            )
            
            st.session_state.current_podcast['script'] = script
        
        # Show the generated script with an edit option
        st.success("Script generated successfully!")
        if podcast_data['edit_script']:
            st.markdown("### Edit Script")
            edited_script = st.text_area("Make any changes to the script:", script, height=300)
            st.session_state.current_podcast['script'] = edited_script
            
            if st.button("Continue with Edited Script"):
                st.session_state.processing_step = "voices"
                st.rerun()
        else:
            st.markdown("### Generated Script Preview")
            st.text_area("Script:", script, height=200, disabled=True)
            
            if st.button("Continue with Generated Script"):
                st.session_state.processing_step = "voices" 
                st.rerun()
    
    # Handle voice generation
    elif st.session_state.processing_step == "voices":
        st.markdown("### Step 2: Generating Character Voices")
        podcast_data = st.session_state.current_podcast
        
        with st.spinner("Converting script to character voices..."):
            voice_data = generate_voices_with_gtts(
                podcast_data['script'],
                podcast_data['voices']
            )
            
            st.session_state.current_podcast['voice_data'] = voice_data
        
        # Show voice preview
        st.success("Voices generated successfully!")
        st.markdown("### Voice Previews")
        
        # Show available audio files
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]
        
        for i, (character, audio_file) in enumerate(voice_data['audio_files'].items()):
            if audio_file:
                with columns[i % 3]:
                    character_name = character
                    if character == "NARRATOR":
                        character_name = f"Narrator ({podcast_data['voices']['narrator']})"
                    elif character == "CHARACTER1":
                        character_name = f"Character 1 ({podcast_data['voices']['character1']})"
                    elif character == "CHARACTER2":
                        character_name = f"Character 2 ({podcast_data['voices']['character2']})"
                    
                    st.markdown(f"#### {character_name}")
                    try:
                        st.audio(audio_file, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Could not play audio: {str(e)}")
        
        if st.button("Continue to Final Assembly"):
            st.session_state.processing_step = "assemble" 
            st.rerun()
    
    # Handle final assembly
    elif st.session_state.processing_step == "assemble":
        st.markdown("### Final Step: Assembling Podcast")
        podcast_data = st.session_state.current_podcast
        
        # Mix all audio and video elements
        with st.spinner("Assembling podcast and creating video..."):
            # Get required data
            voice_data = podcast_data.get('voice_data', {})
            script = podcast_data.get('script', '')
            
            # Assemble final podcast audio
            final_data = assemble_podcast(voice_data, script)
            st.session_state.current_podcast['final_data'] = final_data
            
            # Generate cover artwork
            with st.spinner("Creating podcast artwork..."):
                artwork = generate_artwork(podcast_data['theme'], podcast_data['art_style'])
                
                # Save the artwork temporarily
                artwork_path = f"temp_artwork_{uuid.uuid4()}.png"
                artwork.save(artwork_path)
                st.session_state.current_podcast['artwork_path'] = artwork_path
                
            # Create the video if requested
            if podcast_data['include_video'] and final_data.get('audio_file'):
                with st.spinner("Creating video with artwork background..."):
                    video_data = create_simple_video(artwork_path, final_data['audio_file'])
                    st.session_state.current_podcast['video_data'] = video_data
            
            # Generate show notes if requested
            if podcast_data['generate_notes']:
                with st.spinner("Generating show notes..."):
                    show_notes = generate_show_notes(script)
                    st.session_state.current_podcast['show_notes'] = show_notes
        
        st.success("Podcast assembly complete!")
        
        # Display the final podcast
        st.markdown("## Your Finished Podcast")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(artwork_path, use_container_width=True, caption=f"Podcast Artwork: {podcast_data['theme']}")
        
        with col2:
            st.markdown(f"### {podcast_data['theme']}")
            st.markdown(f"**Style:** {podcast_data['tone']} | **Length:** {final_data.get('duration', 'N/A')}")
            
            # Display audio player
            if final_data.get('audio_file'):
                st.audio(final_data['audio_file'], format="audio/mp3")
            else:
                st.error("Audio file not available")
            
            # Display video if created
            if podcast_data['include_video'] and podcast_data.get('video_data', {}).get('video_path'):
                st.video(podcast_data['video_data']['video_path'])
        
        # Show notes section
        if podcast_data.get('show_notes'):
            st.markdown("### Show Notes")
            st.text_area("Show Notes", podcast_data['show_notes'], height=200)
            
            if st.download_button(
                "Download Show Notes", 
                podcast_data['show_notes'], 
                file_name=f"show_notes_{podcast_data['theme'].replace(' ', '_')}.md",
                mime="text/markdown"
            ):
                st.success("Show notes downloaded!")
        
        # Save and publish options
        st.markdown("### Save & Publish")
        col_save1, col_save2 = st.columns(2)
        
        with col_save1:
            podcast_name = st.text_input("Save Podcast As", f"{podcast_data['theme']}")
            
            if st.button("Save Podcast"):
                # Save podcast data
                podcast_id = save_podcast({
                    "name": podcast_name,
                    "theme": podcast_data['theme'],
                    "audio_file": final_data.get('audio_file'),
                    "artwork_path": podcast_data.get('artwork_path'),
                    "show_notes": podcast_data.get('show_notes'),
                    "video_path": podcast_data.get('video_data', {}).get('video_path')
                })
                
                if podcast_id:
                    st.success(f"Podcast saved successfully! ID: {podcast_id}")
                else:
                    st.error("Error saving podcast")
        
        with col_save2:
            if podcast_data['auto_publish']:
                st.info("Auto-publishing is enabled but not yet implemented in this version")
            
            st.download_button(
                "Download Audio File",
                data=open(final_data['audio_file'], 'rb').read(),
                file_name=f"{podcast_name.replace(' ', '_')}.mp3",
                mime="audio/mp3"
            )
            
            if podcast_data['include_video'] and podcast_data.get('video_data', {}).get('video_path'):
                st.download_button(
                    "Download Video File",
                    data=open(podcast_data['video_data']['video_path'], 'rb').read(),
                    file_name=f"{podcast_name.replace(' ', '_')}.mp4",
                    mime="video/mp4"
                )
        
        # Button to create a new podcast
        if st.button("Create New Podcast"):
            st.session_state.processing_step = None
            st.session_state.current_podcast = {}
            st.rerun()

def view_podcasts_page():
    st.markdown("# Your Podcasts")
    st.info("This section would display your previously created podcasts. Feature not implemented in this version.")
    
    # Placeholder for podcast library
    st.markdown("### Podcast Library")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Sample Podcast 1")
        st.image("https://via.placeholder.com/150", use_container_width=True)
        st.markdown("Space Adventures")
        st.markdown("Duration: 12:34")
        st.button("Play", key="play1")
    
    with col2:
        st.markdown("#### Sample Podcast 2")
        st.image("https://via.placeholder.com/150", use_container_width=True)
        st.markdown("Mystery Theater")
        st.markdown("Duration: 8:45")
        st.button("Play", key="play2")
    
    with col3:
        st.markdown("#### Sample Podcast 3")
        st.image("https://via.placeholder.com/150", use_container_width=True)
        st.markdown("Science Show")
        st.markdown("Duration: 15:20")
        st.button("Play", key="play3")

def about_page():
    st.markdown("# About PodGenie")
    st.markdown("""
    ## AI-Powered Podcast Generator
    
    PodGenie uses artificial intelligence to help you create engaging podcasts with just a few clicks.
    
    ### Features:
    - Generate complete podcast scripts
    - Create natural-sounding voice narration
    - Produce podcast artwork
    - Assemble professional-quality audio
    - Create video podcasts with artwork backgrounds
    - Generate comprehensive show notes
    
    ### Technology:
    - Text-to-Speech: Google Text-to-Speech (gTTS)
    - Image Generation: Stability AI's SDXL
    - Audio Processing: PyDub
    - Video Creation: MoviePy
    - User Interface: Streamlit
    
    This is a demonstration version with simplified functionality.
    """)
    
    st.markdown("### Credits")
    st.markdown("Created by AI Assistant - 2024")

# Main application
def main():
    st.set_page_config(
        page_title="PodGenie - AI Podcast Generator",
        page_icon="🎙️",
        layout="wide"
    )
    
    # App sidebar
    st.sidebar.title("PodGenie")
    st.sidebar.markdown("AI-Powered Podcast Creator")
    
    # Navigation
    page = st.sidebar.radio("Navigation", ["Create New Podcast", "Your Podcasts", "About"])
    
    # Initialize session state for navigation
    if 'page' not in st.session_state:
        st.session_state.page = page
    
    # Render the appropriate page
    if page == "Create New Podcast":
        create_podcast_page()
    elif page == "Your Podcasts":
        view_podcasts_page()
    elif page == "About":
        about_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2024 PodGenie")
    st.sidebar.info("This is a demonstration of AI-powered podcast creation.")

if __name__ == "__main__":
    main()