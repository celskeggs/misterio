<?php
$req_admin = FALSE;
$get_json = FALSE;
require("access.php");
set_json();
if (!isset($_GET['offset']) || !isset($_GET['limit']) || !isset($_GET['scope'])) {
	die_error(400, "Should have offset, limit, AND scope!");
}
$is_inbox = $_GET['scope'] == "inbox";
$is_count = $_GET['scope'] == "count";
if (!$is_inbox && !$is_count && $_GET['scope'] != "all") {
	die_error(400, "Expected either scope=inbox or scope=count or scope=all!");
}
// Inbox is all the posts addressed to you but not replied to.
$posts_offset = intval($_GET['offset']);
$posts_limit = intval($_GET['limit']);
$query_inbox_count = "SELECT COUNT(`UID`) FROM `Posts`,`PostRecipients` WHERE `PostID`=`UID` AND `RecipientID`=? AND `RecipientID`=? AND `UID` NOT IN (SELECT `ResponseTo` FROM `Posts` WHERE `ResponseTo` IS NOT NULL GROUP BY `ResponseTo`)";
if ($is_inbox) {
	$query_input_text = "SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` , `RecipientID` FROM ( SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` FROM `Posts`,`PostRecipients` WHERE `PostID`=`UID` AND `RecipientID`=? AND `RecipientID`=? AND `UID` NOT IN (SELECT `ResponseTo` FROM `Posts` WHERE `ResponseTo` IS NOT NULL GROUP BY `ResponseTo`) GROUP BY `PostID` ORDER BY `Date` DESC LIMIT ?, ? ) AS `Main` LEFT JOIN `PostRecipients` ON ( `UID` = `PostID` )";
	$query_count_text = $query_inbox_count;
	// TODO: Check that query!
	// RecipientID clause duplicated so that I can use the same parameter binding for all three queries
} else if ($is_count) {
	$query_count_text = $query_inbox_count;
} else if ($user_admin) { // Show all posts to the administrator
	$query_input_text = "SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` , `RecipientID` FROM ( SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` FROM `Posts` WHERE ? = ? GROUP BY `UID` ORDER BY `Date` DESC LIMIT ?, ? ) AS `Main` LEFT JOIN `PostRecipients` ON ( `UID` = `PostID` )";
	$query_count_text = "SELECT COUNT(`UID`) FROM `Posts` WHERE ? = ?";
	// ? = ? clause added so that I can use the same parameter binding for all three queries
} else {
	$query_input_text = "SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` , `RecipientID` FROM ( SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` FROM `Posts` LEFT JOIN `PostRecipients` ON ( `PostID` = `UID` ) WHERE ( `IsPublic` = 1 OR `Author` = ? OR `RecipientID` = ? ) GROUP BY `UID` ORDER BY `Date` DESC LIMIT ? , ? ) AS `Main` LEFT JOIN `PostRecipients` ON ( `UID` = `PostID` )";
	$query_count_text = "SELECT COUNT(`UID`) FROM (SELECT DISTINCT `UID` FROM `Posts` LEFT JOIN `PostRecipients` ON ( `PostID` = `UID` ) WHERE ( `IsPublic` = 1 OR `Author` = ? OR `RecipientID` = ? )) as `Main`";
}
$qry_count = $db->prepare($query_count_text);
if ($qry_count === FALSE || !$qry_count->bind_param("ii", $user_uid, $user_uid) || !$qry_count->execute() || !$qry_count->bind_result($query_count_count) || !$qry_count->fetch()) {
	die_error(500, "Server Error: Could not submit count query.");
}
$post_total = $query_count_count;
if (!$qry_count->close()) {
	die_error(500, "Server Error: Could not finish count query.");
}
if ($is_count) {
	echo json_encode(array('inbox' => $post_total));
	exit;
}
$qry = $db->prepare($query_input_text);
if ($qry === FALSE || !$qry->bind_param("iiii", $user_uid, $user_uid, $posts_offset, $posts_limit) || !$qry->execute() || !$qry->bind_result($query_uid, $query_ispublic, $query_title, $query_data, $query_author, $query_responseto, $query_date, $query_recipient)) {
	die_error(500, "Server Error: Could not submit body query.");
}
$posts = array();
$uids = array();
while ($qry->fetch()) {
	$post_offset = array_search($query_uid, $uids, true);
	if ($post_offset !== false) {
		if ($query_recipient === null) {
			// Shouldn't happen - this should only be null if there are no recipients, which would mean that it should be the only entry, and $post_offset should be FALSE!
			die_error(500, "Recipient assertion failed");
		}
		$posts[$post_offset]['to'][] = $query_recipient;
		continue;
	}
	$recip = array();
	if ($query_recipient !== null) {
		$recip[] = $query_recipient;
	}
	$post = array('id' => $query_uid, 'public' => ($query_ispublic ? true : false), 'title' => utf8_encode($query_title), 'data' => utf8_encode($query_data), 'from' => $query_author, 'prev' => $query_responseto, 'date' => strtotime($query_date) * 1000, 'to' => $recip);
	$posts[] = $post;
	$uids[] = $query_uid;
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not finish body query.");
}
echo json_encode(array('data' => $posts, 'total' => $post_total));
