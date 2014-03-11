<?php
$req_admin = TRUE;
$get_json = FALSE;
require("access.php");
set_json();
$qry = $db->prepare("TRUNCATE TABLE `Posts`");
if ($qry === FALSE || !$qry->execute()) {
	die_error(500, "Server Error: Could not submit body query.");
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not complete body query.");
}
echo json_encode(array());
