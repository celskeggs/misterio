<?php
$req_admin = FALSE;
$get_json = FALSE;
require("access.php");
set_json();
$users = array();
$filenames = scandir("img");
if ($filenames === FALSE) {
	die_error(500, "Server Error: Could not list directory.");
}
$ignarr = array();
$ignore = @fopen("./img/notavatar.txt", "r");
if ($ignore) {
	while (($buffer = fgets($ignore, 4096)) !== false) {
		$ignarr[] = trim($buffer);
	}
}
fclose($ignore);
$out = array();
foreach ($filenames as $filename) {
  if ($filename[0] !== '.' && !in_array($filename, $ignarr)) {
    $out[] = $filename;
  }
}
echo json_encode($out);
