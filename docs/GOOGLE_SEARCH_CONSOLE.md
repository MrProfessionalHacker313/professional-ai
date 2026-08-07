# GOOGLE SEARCH CONSOLE — Professional AI

## 1. ADD PROPERTY

1. Go to [search.google.com/search-console](https://search.google.com/search-console)
2. Click **Add Property**
3. Select **URL prefix**
4. Enter: `https://professionalai.com`
5. Click **Continue**

## 2. VERIFY OWNERSHIP

Choose one method:

### Method A: DNS TXT Record (Recommended)
1. Copy the TXT record from Google Search Console
2. Go to your domain registrar (e.g., GoDaddy, Namecheap, Cloudflare)
3. Add a new TXT record:
   - Name/Host: `@`
   - Value: `google-site-verification=[CODE]`
   - TTL: 3600
4. Wait 15–30 minutes, then click **Verify** in Search Console

### Method B: HTML File Upload
1. Download the `google[CODE].html` file from Search Console
2. Upload it to the root of your website: `https://professionalai.com/google[CODE].html`
3. Click **Verify**

### Method C: Google Analytics (if already installed)
1. Ensure GA4 is linked to the same Google account
2. Search Console will auto-verify

## 3. SUBMIT SITEMAP

1. In Search Console, go to **Sitemaps** (left menu)
2. Paste: `https://professionalai.com/sitemap.xml`
3. Click **Submit**
4. Status should show "Success" within 24 hours

## 4. REQUEST INDEXING FOR PRIORITY PAGES

Submit these URLs for immediate indexing:

1. **Homepage:** `https://professionalai.com`
2. **Pricing:** `https://professionalai.com/pricing`
3. **Features:** `https://professionalai.com/features`
4. **Download:** `https://professionalai.com/download`
5. **Blog:** `https://professionalai.com/blog`

Steps:
1. Go to **URL Inspection** (top search bar)
2. Paste each URL
3. Click **Request Indexing**
4. Repeat for all 5 URLs

## 5. CONFIGURE PERFORMANCE REPORTS

1. Go to **Performance** (left menu)
2. Set date range: Last 28 days
3. Key metrics to track:
   - **Clicks:** How many users click your result
   - **Impressions:** How many times your page appears
   - **CTR:** Click-through rate (aim for >5%)
   - **Average position:** Target top 10 for primary keywords

## 6. LINK TO GOOGLE ANALYTICS

1. Go to **Settings** → **Associations**
2. Click **Associate with Google Analytics**
3. Select your GA4 property
4. This allows you to see organic traffic alongside conversions

## 7. MONITOR INDEXING STATUS

- **Pages:** Should show all submitted pages as "Indexed"
- **Crawl errors:** Fix any 404s or server errors immediately
- **Mobile usability:** Ensure no mobile issues (already responsive)
- **Core Web Vitals:** Check for "Poor" or "Needs Improvement" ratings

## 8. URL PARAMETERS

If using query parameters (e.g., `?lang=ur`), ensure they are not causing duplicate content issues:
- Go to **Settings** → **Crawl** → **URL Parameters**
- Add `lang` parameter with "Doesn't affect page content" (since it's just language switching)

## 9. COUNTRY TARGETING

1. Go to **Settings** → **International Targeting**
2. Set **Country target** to **Pakistan** (primary) + **United States** (secondary)
3. Add hreflang tags for all supported languages (already implemented in layout.tsx)

## 10. SECURITY & MANUAL ACTIONS

- Check **Security Issues** tab regularly
- Check **Manual Actions** tab for any Google penalties
- Keep SSL certificate valid (TLS 1.3 already enabled)

## 11. SITEMAP LOCATION

Ensure your `robots.txt` includes the sitemap reference:
```
Sitemap: https://professionalai.com/sitemap.xml
```

## 12. STRUCTURED DATA VALIDATION

Test your schema markup:
1. Go to [Google Rich Results Test](https://search.google.com/test/rich-results)
2. Enter: `https://professionalai.com`
3. Verify no errors in SoftwareApplication, FAQPage, Organization, Review schemas

---

✅ GOOGLE SEARCH CONSOLE SETUP COMPLETE — homepage, pricing, features, download, and blog pages are submitted for indexing.
