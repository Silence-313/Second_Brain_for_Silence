"""Tests for storage infrastructure."""

import pytest

from agent.infrastructure.storage.memory_fs import InMemoryFileStorage


class TestInMemoryFileStorage:
    @pytest.mark.asyncio
    async def test_write_read(self) -> None:
        fs = InMemoryFileStorage()
        await fs.write("/test/file.md", "hello world")
        content = await fs.read("/test/file.md")
        assert content == "hello world"

    @pytest.mark.asyncio
    async def test_exists(self) -> None:
        fs = InMemoryFileStorage()
        await fs.write("/test/file.md", "hello")
        assert await fs.exists("/test/file.md")
        assert not await fs.exists("/test/nonexistent.md")

    @pytest.mark.asyncio
    async def test_list_dir(self) -> None:
        fs = InMemoryFileStorage()
        await fs.write("/test/file1.md", "a")
        await fs.write("/test/file2.md", "b")
        await fs.write("/other/file3.md", "c")
        files = await fs.list_dir("/test")
        assert "file1.md" in files
        assert "file2.md" in files
        assert "file3.md" not in files

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        fs = InMemoryFileStorage()
        await fs.write("/test/file.md", "hello")
        await fs.delete("/test/file.md")
        assert not await fs.exists("/test/file.md")

    @pytest.mark.asyncio
    async def test_mkdir(self) -> None:
        fs = InMemoryFileStorage()
        await fs.mkdir("/new/dir")
        # mkdir is a no-op in memory FS — just verify no error

    @pytest.mark.asyncio
    async def test_read_nonexistent(self) -> None:
        fs = InMemoryFileStorage()
        with pytest.raises(FileNotFoundError):
            await fs.read("/nonexistent.md")

    def test_file_count(self) -> None:
        fs = InMemoryFileStorage()

        async def run():
            await fs.write("/a.md", "a")
            await fs.write("/b.md", "b")
        import asyncio
        asyncio.run(run())
        assert fs.file_count == 2
