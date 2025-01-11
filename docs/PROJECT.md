# Boat Price Tracking System

## Project Overview
Bu proje, tekne kiralama platformlarındaki rakip firmaların fiyatlarını takip eden, analiz eden ve raporlayan bir sistemdir.

### Core Features
1. **Platform Entegrasyonları**
   - [x] Nausys Login İşlemi
   - [x] MMK Booking Manager Login İşlemi
   - [ ] Rakip Firma Seçimi ve Filtreleme
   - [ ] Takvim Üzerinden Tarih Seçimi
   - [ ] Fiyat Verisi Çekme

2. **Web Uygulaması**
   - [ ] Single Page Application (SPA) Arayüzü
   - [ ] Bot Kontrol Paneli (Start/Stop)
   - [ ] Fiyat Karşılaştırma Raporları
   - [ ] Anlık Veri Görüntüleme

3. **Veritabanı**
   - [ ] Fiyat Logları
   - [ ] Rakip Firma Bilgileri
   - [ ] Karşılaştırma Raporları

4. **Bot İşlevleri**
   - [x] Selenium WebDriver Entegrasyonu
   - [x] Headless Mode Desteği
   - [ ] Otomatik Veri Toplama
   - [ ] Fiyat Karşılaştırma Algoritması

### Nice to Have Features
1. **Bildirim Sistemi**
   - [ ] Email Bildirimleri
   - [ ] Fiyat Düşüş/Artış Alertleri
   - [ ] Günlük/Haftalık Rapor Özetleri

2. **Analitik Dashboard**
   - [ ] Fiyat Trend Grafikleri
   - [ ] Rakip Analizi
   - [ ] Sezonsal Fiyat Değişimleri

3. **Gelişmiş Özellikler**
   - [ ] API Entegrasyonu
   - [ ] Çoklu Dil Desteği
   - [ ] Mobil Uyumlu Tasarım
   - [ ] Export Özellikleri (PDF, Excel)

## Completed Tasks
1. **Initial Setup (2024-01-XX)**
   - Proje yapısı oluşturuldu
   - Selenium entegrasyonu yapıldı
   - Docker desteği eklendi

2. **Platform Logins (2024-01-XX)**
   - Nausys login işlemi tamamlandı
   - MMK Booking Manager login işlemi tamamlandı
   - Hata yönetimi ve loglama eklendi

3. **UI Development (2024-01-XX)**
   - Streamlit UI temel yapısı oluşturuldu
   - Mock data ile test edildi
   - Temel komponentler eklendi:
     * Bot kontrol paneli
     * Fiyat karşılaştırma grafiği
     * Detaylı fiyat tablosu
     * Metrik kartları

## Current Status
- [x] UI temel yapısı tamamlandı ve test edildi
- [x] Mock data ile görsel tasarım doğrulandı
- [ ] Backend entegrasyonu bekliyor

## Next Steps
1. **Veri Toplama Sistemi**
   - Rakip firma seçim mekanizması
   - Takvim entegrasyonu
   - Fiyat verisi çekme işlemleri

2. **Web Uygulaması Geliştirme**
   - Frontend framework seçimi (React/Vue.js)
   - Backend API geliştirme (FastAPI/Flask)
   - Veritabanı tasarımı

3. **Bot Geliştirme**
   - Veri toplama algoritması
   - Fiyat karşılaştırma mantığı
   - Otomatik çalışma mekanizması

## Technical Stack (Updated)
- **Backend:** Python (FastAPI)
- **Frontend:** Streamlit (Python-based UI framework)
- **Database:** MongoDB (with Motor async driver)
- **Containerization:** Docker
- **Web Scraping:** Selenium

## Frontend Seçim Nedenleri
Streamlit tercih edildi çünkü:
- Python tabanlı, yeni bir dil öğrenmeye gerek yok
- Minimal kod ile güzel UI oluşturabilme
- Veri görselleştirme araçları built-in
- Kolay deployment
- Real-time güncelleme desteği
- Bot kontrolü için ideal arayüz 

## Project Structure 