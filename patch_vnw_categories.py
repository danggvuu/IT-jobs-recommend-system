import re

with open('scrapers/scraper_vnw.py', 'r') as f:
    content = f.read()

# Replace single base_url with loop
# First, update __init__
init_old = """        self.base_url = vnw_cfg.get(
            "base_url",
            "https://www.vietnamworks.com/viec-lam?q=it-software"
        )"""
init_new = """        self.base_urls = {
            "IT Phần mềm": "https://www.vietnamworks.com/viec-lam?q=it-software",
            "Marketing": "https://www.vietnamworks.com/viec-lam?q=marketing",
            "Sales": "https://www.vietnamworks.com/viec-lam?q=sales"
        }"""
content = content.replace(init_old, init_new)

# Now update run()
run_old = """    def run(self):
        logger.info("════════════════════════════════════════════════════════════")
        logger.info("🏁 BẮT ĐẦU THU THẬP DỮ LIỆU TỪ VIETNAMWORKS.COM")
        logger.info("   URL: %s", self.base_url)
        logger.info("   Số trang tối đa: %d", self.max_pages)
        logger.info("════════════════════════════════════════════════════════════")

        try:
            self.page = self._init_browser()
            logger.info("🌐 Đang truy cập %s ...", self.base_url)
            self.page.get(self.base_url)
            
            # Xử lý popups ban đầu
            self.page.wait.load_start()
            time.sleep(3)
            self._dismiss_popups()

            current_page = 1
            while current_page <= self.max_pages:
                logger.info("────────────────────────────────────────")
                logger.info("📖 Đang xử lý trang %d/%d ...", current_page, self.max_pages)
                
                # Cào data
                jobs_count, should_stop = self._scrape_page(current_page)
                
                if should_stop:
                    logger.info("🛑 Gặp trang không hợp lệ hoặc lỗi, DỪNG cào.")
                    break

                if current_page >= self.max_pages:
                    break

                # Qua trang
                if not self._go_next_page(current_page):
                    logger.info("🔚 Không tìm thấy nút chuyển trang. Đã đến trang cuối.")
                    break
                    
                current_page += 1
                time.sleep(random.uniform(*self.delay_range))

        except Exception as e:
            logger.error("💥 Lỗi nghiêm trọng: %s", e, exc_info=True)
        finally:
            if self.page:
                logger.info("🔒 Trình duyệt đã đóng")
                self.page.quit()

        logger.info("════════════════════════════════════════════════════════════")
        logger.info("✅ HOÀN THÀNH: %d việc làm trong %.1f giây", len(self.jobs), time.time() - self.start_time)
        logger.info("════════════════════════════════════════════════════════════")"""

run_new = """    def run(self):
        logger.info("════════════════════════════════════════════════════════════")
        logger.info("🏁 BẮT ĐẦU THU THẬP DỮ LIỆU TỪ VIETNAMWORKS.COM")
        logger.info("   Số trang tối đa mỗi ngành: %d", self.max_pages)
        logger.info("════════════════════════════════════════════════════════════")

        try:
            self.page = self._init_browser()
            
            for industry_name, base_url in self.base_urls.items():
                logger.info("\\n🌟 Bắt đầu cào ngành: %s", industry_name)
                logger.info("🌐 Đang truy cập %s ...", base_url)
                self.page.get(base_url)
                
                # Xử lý popups ban đầu
                self.page.wait.load_start()
                time.sleep(3)
                self._dismiss_popups()
                
                # Set industry name globally for this loop iteration so _scrape_page can use it
                self.current_industry = industry_name

                current_page = 1
                while current_page <= self.max_pages:
                    logger.info("────────────────────────────────────────")
                    logger.info("📖 Đang xử lý trang %d/%d (Ngành: %s)...", current_page, self.max_pages, industry_name)
                    
                    # Cào data
                    jobs_count, should_stop = self._scrape_page(current_page)
                    
                    if should_stop:
                        logger.info("🛑 Gặp trang không hợp lệ hoặc lỗi, DỪNG cào ngành này.")
                        break

                    if current_page >= self.max_pages:
                        break

                    # Qua trang
                    if not self._go_next_page(current_page, base_url):
                        logger.info("🔚 Không tìm thấy nút chuyển trang. Đã đến trang cuối của ngành này.")
                        break
                        
                    current_page += 1
                    time.sleep(random.uniform(*self.delay_range))

        except Exception as e:
            logger.error("💥 Lỗi nghiêm trọng: %s", e, exc_info=True)
        finally:
            if self.page:
                logger.info("🔒 Trình duyệt đã đóng")
                self.page.quit()

        logger.info("════════════════════════════════════════════════════════════")
        logger.info("✅ HOÀN THÀNH TỔNG CỘNG: %d việc làm trong %.1f giây", len(self.jobs), time.time() - self.start_time)
        logger.info("════════════════════════════════════════════════════════════")"""
content = content.replace(run_old, run_new)

# Update _go_next_page signature to take base_url
content = content.replace("def _go_next_page(self, current_page: int) -> bool:", "def _go_next_page(self, current_page: int, base_url: str) -> bool:")
content = content.replace("self.base_url", "base_url")

# Update 'VietnamWorks' hardcoded industry to self.current_industry in _scrape_page
content = content.replace("now_str, now_str, 'VietnamWorks', job[\"url\"],", "now_str, now_str, getattr(self, 'current_industry', 'VietnamWorks'), job[\"url\"],")

with open('scrapers/scraper_vnw.py', 'w') as f:
    f.write(content)
print("Updated categories!")
