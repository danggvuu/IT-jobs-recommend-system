import re

with open('scrapers/scraper_vnw.py', 'r') as f:
    content = f.read()

restart_logic = """
            except Exception as e:
                logger.warning("  ⚠️  [%d/%d] Lỗi trích xuất: %s", idx, len(cards), e)
                if 'Disconnected' in str(e) or '断开' in str(e):
                    logger.error("💥 Trình duyệt bị văng! Khởi động lại...")
                    try:
                        self.page.quit()
                    except:
                        pass
                    import time
                    time.sleep(3)
                    self.page = self._init_browser()
                    minimize_browser(self.page)
                    # Phải break ra để vòng lặp ngoài tải lại trang hiện tại, hoặc bỏ qua trang này
                    return page_jobs
                continue
"""

content = re.sub(r'            except Exception as e:\n                logger.warning\("  ⚠️  \[%d/%d\] Lỗi trích xuất: %s", idx, len\(cards\), e\)\n                continue', restart_logic, content)

with open('scrapers/scraper_vnw.py', 'w') as f:
    f.write(content)
