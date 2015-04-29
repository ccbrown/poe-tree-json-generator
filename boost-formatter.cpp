#include <boost/format.hpp>

#include <iostream>

int main (int argc, char* argv[]) {
	boost::format format(argv[1]);
	format.exceptions(boost::io::all_error_bits ^ boost::io::too_many_args_bit);
	for (int i = 2; i < argc; ++i) {
		format % argv[i];
	}
	std::cout << format;
	return 0;
}