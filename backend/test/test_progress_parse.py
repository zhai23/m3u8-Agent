import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.core.downloader import M3U8下载器


class TestProgressParse(unittest.TestCase):
    def setUp(self):
        self.下载器 = object.__new__(M3U8下载器)

    def test_parse_new_format(self):
        行 = "Vid 1280x720 | 0 Kbps ------------------------------ 523/739 70.77% 153.99MB/228.51MB 15.76MBps 00:00:03"
        结果 = self.下载器._解析进度(行)
        self.assertIsNotNone(结果)
        self.assertAlmostEqual(结果["percent"], 70.77, places=2)
        self.assertEqual(结果["speed"], "15.76 MB/s")
        self.assertEqual(结果["eta"], "00:00:03")

    def test_parse_new_format_with_trailing_slash(self):
        行 = "Vid 1280x720 | 0 Kbps ------------------------------ 138/739 18.67% 50.73MB/271.66MB 1.70MBps 00:01:49 /"
        结果 = self.下载器._解析进度(行)
        self.assertIsNotNone(结果)
        self.assertAlmostEqual(结果["percent"], 18.67, places=2)
        self.assertEqual(结果["speed"], "1.70 MB/s")
        self.assertEqual(结果["eta"], "00:01:49")

    def test_parse_old_format(self):
        行 = "[12:34:56] 45.5% | 2.5 MB/s | ETA: 00:02:30"
        结果 = self.下载器._解析进度(行)
        self.assertIsNotNone(结果)
        self.assertAlmostEqual(结果["percent"], 45.5, places=1)
        self.assertEqual(结果["speed"], "2.5 MB/s")
        self.assertEqual(结果["eta"], "00:02:30")

    def test_no_percent_returns_none(self):
        行 = "Vid 1280x720 | 0 Kbps"
        结果 = self.下载器._解析进度(行)
        self.assertIsNone(结果)


if __name__ == "__main__":
    unittest.main()
