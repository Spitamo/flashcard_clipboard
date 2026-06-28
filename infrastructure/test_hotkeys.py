from unittest.mock import patch

from hotkeys import HotkeyListener


@patch("hotkeys.threading.Thread")
def test_start_does_not_create_second_thread(mock_thread):
    fake_thread = mock_thread.return_value
    fake_thread.is_alive.return_value = True

    listener = HotkeyListener("ctrl+c", 0)
    listener._thread = fake_thread

    listener.start()

    mock_thread.assert_not_called()