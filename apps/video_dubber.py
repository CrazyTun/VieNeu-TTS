import gradio as gr
from moviepy import VideoFileClip, AudioFileClip
from vieneu import Vieneu
import os
import tempfile

# Initialize Vieneu TTS
vieneu = Vieneu()

def process_video(video_path, target_text, voice_id):
    if not video_path:
        return None, "Vui lòng tải lên một video."

    try:
        # Load video
        video = VideoFileClip(video_path)

        # 1. Extract audio from video to use as reference voice
        # Ensure temporary files don't conflict
        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_audio_path = temp_audio_file.name
        temp_audio_file.close()

        if video.audio is None:
            return None, "Video không có âm thanh để clone giọng."

        # Save audio from video
        video.audio.write_audiofile(temp_audio_path, logger=None)

        # 2. Use Vieneu to clone voice and generate new speech
        print(f"Cloning voice and generating text: '{target_text}'")

        if voice_id and voice_id != "Từ Video":
            # Use preset voice if selected
            print(f"Using preset voice: {voice_id}")
            new_audio_array = vieneu.infer(target_text, voice=voice_id)
        else:
            # Clone from the video's audio
            print(f"Cloning from video audio")
            new_audio_array = vieneu.infer(target_text, ref_audio=temp_audio_path)

        # Save the generated audio
        temp_new_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_new_audio_path = temp_new_audio_file.name
        temp_new_audio_file.close()

        vieneu.save(new_audio_array, temp_new_audio_path)

        # 3. Replace video's audio with the new audio
        new_audio_clip = AudioFileClip(temp_new_audio_path)

        final_video = video.with_audio(new_audio_clip)

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        output_path = output_file.name
        output_file.close()

        # Write final video
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        # Clean up temp files
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if os.path.exists(temp_new_audio_path):
            os.remove(temp_new_audio_path)

        return output_path, "Xử lý thành công!"

    except Exception as e:
        return None, f"Lỗi: {str(e)}"

# Get preset voices for dropdown
preset_voices = [("Từ Video", "Từ Video")]
try:
    voices = vieneu.list_preset_voices()
    preset_voices.extend([(label, vid) for label, vid in voices])
except Exception as e:
    print(f"Could not load preset voices: {e}")

def create_ui():
    with gr.Blocks(title="VieNeu Video Dubber") as app:
        gr.Markdown("# 🎬 Video Voice Dubber")
        gr.Markdown("Tải lên một video, ứng dụng sẽ tách giọng từ video đó và lồng tiếng lại với nội dung mới!")

        with gr.Row():
            with gr.Column():
                video_input = gr.Video(label="Video Gốc (Cần có âm thanh giọng nói rõ ràng)")
                text_input = gr.Textbox(
                    label="Nội dung muốn đọc mới",
                    lines=4,
                    placeholder="Nhập nội dung bạn muốn nhân vật trong video đọc..."
                )
                voice_dropdown = gr.Dropdown(
                    choices=[v[1] for v in preset_voices],
                    value="Từ Video",
                    label="Chọn Giọng (Hoặc giữ 'Từ Video' để clone)"
                )
                process_btn = gr.Button("Xử lý Video", variant="primary")

            with gr.Column():
                video_output = gr.Video(label="Video Kết Quả")
                status_output = gr.Textbox(label="Trạng thái", interactive=False)

        process_btn.click(
            fn=process_video,
            inputs=[video_input, text_input, voice_dropdown],
            outputs=[video_output, status_output]
        )

    return app

def main():
    print("Starting Video Dubber App...")
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7861)

if __name__ == "__main__":
    main()
