# build_c_files
# Loops through the '$LESDIR/src/libsrc/usrint' to read the .c files.
# creates the makefile based on the .c and .o files available in '$LESDIR/src/libsrc/usrint'
# Input  : path of the .c & .o files 
# Output : creates the makefile in Usrint directory with the updated files list 
use Getopt::Std;
use File::Basename;

sub GetFullPath
{
    my $path = shift;
   
    $path =~ s/\$(\w+)/$ENV{$1}/g; 

    return $path;
}

#--------------------------------- Main function : Begins-------------------------------------------

my $directory;
my @cfiles; 
my $cfile; 
my $count;
my $dstnDir;
my $makefile;

$directory = join(' ', @ARGV);

if ($directory eq "")
{
  $directory = ".";
}

$directory = GetFullPath($directory);
if ($directory != ".")
{
	$dstnDir = basename($directory);
	print $dstnDir,"\n";
	
	# Get the correct case for the destination directory
	if ($dstnDir eq "usrint")
	{
		$dstnDir = "USRint"; 
		print $dstnDir,"\n";
	}
}
else
{
	$dstnDir = "USRint";
	$directory = GetFullPath('$LESDIR/src/libsrc/usrint');
	#print $directory,"\n";
}

# Get to the destination directory
chdir("$directory") or die "\n Error : Could not change the directory to $directory. \n";

# Open the destination directory
opendir(DESTN, ".") || die "\n Error : Could not open the destination directory. \n";
@cfiles = readdir(DESTN);
 
$count = 0;
$makefile = "";
# Loop through the directory to get the .c files
foreach $cfile (@cfiles)
{
	if ($cfile =~ /(.*)\.c$/)
	{
		if ($count++ > 0)
		{
			$makefile .= " \\\n";
			#print $makefile,"\n"; 
      	}
		$makefile .= "$1.o";
	}
}
close(DESTN);

if (!$count)
{
	print "Error : No '.c' files found.\n";
	exit;
}
$makefile .= " \n\n";

# Write makfile if we have count is not Zero
open(MAKEFH, ">makefile") || die "Could not open makefile.\n";

print MAKEFH "LESDIR=../../..";
print MAKEFH "\n\n";
print MAKEFH "include \$\(LESDIR)/makefiles/StandardHeader.mk\n\n";
print MAKEFH "LIBNAME=$dstnDir\n\n";
print MAKEFH "OFILES=";
print MAKEFH "$makefile";
print MAKEFH "include \$\(LESDIR)/makefiles/Component.mk\n";
print MAKEFH "include \$\(LESDIR)/makefiles/StandardFooter.mk\n";

close MAKEFH;
