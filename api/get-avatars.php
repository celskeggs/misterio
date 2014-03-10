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
$out = array();
foreach ($filenames as $filename) {
  if ($filename[0] !== '.') {
    $out[] = $filename;
  }
}
echo json_encode($out);
