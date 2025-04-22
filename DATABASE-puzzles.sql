/*
 Navicat Premium Data Transfer

 Source Server         : mysql_localhost
 Source Server Type    : MySQL
 Source Server Version : 100404
 Source Host           : localhost:3306
 Source Schema         : q3

 Target Server Type    : MySQL
 Target Server Version : 100404
 File Encoding         : 65001

 Date: 22/04/2025 21:26:30
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for puzzles
-- ----------------------------
DROP TABLE IF EXISTS `puzzles`;
CREATE TABLE `puzzles`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `date` timestamp(0) NOT NULL DEFAULT current_timestamp(0),
  `tags` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `grid` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `clues` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `solution_key` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `author_id` int(11) NULL DEFAULT NULL,
  `solved_count` int(11) NULL DEFAULT 0,
  `last_solved` timestamp(0) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `author_id`(`author_id`) USING BTREE,
  CONSTRAINT `puzzles_ibfk_1` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of puzzles
-- ----------------------------

-- ----------------------------
-- Table structure for submissions
-- ----------------------------
DROP TABLE IF EXISTS `submissions`;
CREATE TABLE `submissions`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NULL DEFAULT NULL,
  `puzzle_id` int(11) NULL DEFAULT NULL,
  `grid_submitted` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `time_taken` float NOT NULL,
  `result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `incorrect_cells` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `timestamp` timestamp(0) NOT NULL DEFAULT current_timestamp(0),
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  INDEX `puzzle_id`(`puzzle_id`) USING BTREE,
  CONSTRAINT `submissions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `submissions_ibfk_2` FOREIGN KEY (`puzzle_id`) REFERENCES `puzzles` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of submissions
-- ----------------------------

-- ----------------------------
-- Table structure for user_stats
-- ----------------------------
DROP TABLE IF EXISTS `user_stats`;
CREATE TABLE `user_stats`  (
  `user_id` int(11) NOT NULL,
  `puzzles_solved` int(11) NULL DEFAULT 0,
  `avg_time` float NULL DEFAULT 0,
  `last_login` timestamp(0) NULL DEFAULT NULL,
  PRIMARY KEY (`user_id`) USING BTREE,
  CONSTRAINT `user_stats_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_stats
-- ----------------------------

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `password_hash` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `created_at` timestamp(0) NOT NULL DEFAULT current_timestamp(0),
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
