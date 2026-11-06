# Put all intermediate/auxiliary files in build/
$aux_dir = 'build';
$out_dir = 'build';

# Copy the final PDF back to the source directory after each build
$success_cmd = 'cp build/%R.pdf %R.pdf';
