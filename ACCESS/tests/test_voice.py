from unittest import TestCase

from voice import VoiceService


class VoiceServiceTests(TestCase):
    def test_configuration_is_bounded(self):
        service = VoiceService()
        service.configure(rate=500, volume=-1, microphone_index=3, voice_id="voice")
        self.assertEqual(320, service.rate)
        self.assertEqual(0.0, service.volume)
        self.assertEqual(3, service.microphone_index)
        self.assertEqual("voice", service.voice_id)

    def test_visual_formatting_is_removed_before_speech(self):
        text = VoiceService._prepare_for_speech(
            "**Open** https://example.com\n```python\nprint('hidden')\n```"
        )
        self.assertEqual("Open link Code block omitted.", text)
