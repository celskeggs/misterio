<?php
$req_admin = TRUE;
$get_json = FALSE;
require("access.php");
set_json();
// Inbox is all the posts addressed to you but not replied to.
$query_text = "SELECT `Players`.`Name` as `UserID`, `Email`, `Players`.`Instance`, COUNT(`Posts`.`UID`) as `PostCNT` FROM `Players`,`Posts`,`PostRecipients` WHERE `Posts`.`IsFinish` = 0 AND `Posts`.`Instance` = `Players`.`Instance` AND `PostID`=`Posts`.`UID` AND `RecipientID`=`Players`.`UID` AND `Posts`.`UID` NOT IN (SELECT `ResponseTo` FROM `Posts` WHERE `ResponseTo` IS NOT NULL GROUP BY `ResponseTo`) GROUP BY `Players`.`UID` ORDER BY `Instance`, `UserID`";
$qry = $db->prepare($query_text);
if ($qry === FALSE || !$qry->execute() || !$qry->bind_result($q_uid, $q_email, $q_inst, $q_cnt)) {
	die_error(500, "Server Error: Could not submit count query.");
}
$counts = array();
while ($qry->fetch()) {
	$counts[] = array("uid" => utf8_encode($q_uid), "email" => $q_email, "inst" => $q_inst, "count" => $q_cnt);
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not finish count query.");
}
echo json_encode($counts);
