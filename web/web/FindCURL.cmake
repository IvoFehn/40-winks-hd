# The browser build does not expose RecompFrontend's native mod downloader.
set(CURL_FOUND TRUE)
add_library(CURL::libcurl INTERFACE IMPORTED)
target_include_directories(CURL::libcurl INTERFACE "${CMAKE_CURRENT_LIST_DIR}")
