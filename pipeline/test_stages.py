import asyncio
import pytest
from unittest.mock import Mock

from domain.models import WordItem
from pipeline.stages import translator_worker


@pytest.mark.asyncio
async def test_translator_worker_puts_translation_into_queue():
    raw_queue = asyncio.Queue()
    translated_queue = asyncio.Queue()

    translator_service = Mock()
    translator_service.translate.return_value = "سلام"

    worker_task = asyncio.create_task(
        translator_worker(
            raw_queue=raw_queue,
            translated_queue=translated_queue,
            translator_service=translator_service,
            source_lang="en",
            target_lang="fa",
        )
    )

    try:
        await raw_queue.put(
            WordItem(
                text="hello",
                captured_at=123.0,
            )
        )

        result = await asyncio.wait_for(
            translated_queue.get(),
            timeout=1,
        )

        assert result.source_text == "hello"
        assert result.translated_text == "سلام"
        assert result.source_lang == "en"
        assert result.target_lang == "fa"

        translator_service.translate.assert_called_once_with(
            "hello",
            "en",
            "fa",
        )
    finally:
        worker_task.cancel()