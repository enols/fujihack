// Based on guessing addresses of screen buffers, will probably change soon
#include "fujihack.h"
#include "fujifilm.h"

// This is all a bunch of crap
#if 1

uint32_t screen_buffer = GET_SCREEN_LAYER(0);

void disp_pixel(int x, int y, int col) {
	uint32_t *buf = (uint32_t *)screen_buffer;
	buf[SCREEN_WIDTH * y + x] = col;
}

void disp_clear(int col) {
	uint32_t *buf = (uint32_t *)screen_buffer;
	for (int i = 0; i < SCREEN_WIDTH * SCREEN_HEIGHT; i++) {
		buf[i] = col;
	}
}

void disp_rect(int x1, int y1, int w1, int h1, int col) {
	for (int x = x1; x < w1+x1; x++) {
		for (int y = y1; y < h1+y1; y++) {
			disp_pixel(x, y, col);
		}
	}
}

#define CONSOLE_MAX 10

int console_curr = 0;

void console_log(char string[]) {
	fuji_screen_write(string, 1, 1 + console_curr, TEXT_BLACK, TEXT_WHITE);
	console_curr++;

	if (console_curr > 9) {
		console_curr = 0;
		fuji_discard_text_buffer();
	}
}

#endif
