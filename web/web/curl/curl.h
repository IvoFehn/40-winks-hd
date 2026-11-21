#pragma once

// The native mod downloader is disabled in the browser build.
using CURL = void;
using CURLcode = int;
struct curl_slist;
constexpr CURLcode CURLE_OK = 0;
constexpr long CURL_GLOBAL_DEFAULT = 0;
enum {
    CURLOPT_URL, CURLOPT_FOLLOWLOCATION, CURLOPT_HTTPHEADER, CURLOPT_SSL_VERIFYHOST,
    CURLOPT_SSL_VERIFYPEER, CURLOPT_TIMEOUT, CURLOPT_USERAGENT, CURLOPT_WRITEDATA,
    CURLOPT_WRITEFUNCTION, CURLINFO_RESPONSE_CODE
};
inline CURLcode curl_global_init(long) { return 1; }
inline CURL* curl_easy_init() { return nullptr; }
inline CURLcode curl_easy_setopt(CURL*, int, ...) { return 1; }
inline CURLcode curl_easy_perform(CURL*) { return 1; }
inline CURLcode curl_easy_getinfo(CURL*, int, ...) { return 1; }
inline void curl_easy_cleanup(CURL*) {}
inline const char* curl_easy_strerror(CURLcode) { return "Mod downloads are unavailable in the browser build."; }
inline curl_slist* curl_slist_append(curl_slist*, const char*) { return nullptr; }
inline void curl_slist_free_all(curl_slist*) {}
