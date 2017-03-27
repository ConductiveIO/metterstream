CREATE TABLE IF NOT EXISTS "tblTweet" (
  "id" INTEGER PRIMARY KEY, 
  "text" VARCHAR(150) NOT NULL,
  "user" VARCHAR(30) NOT NULL,
  "screen_name" VARCHAR(30) NOT NULL,
  "profile_image_url" VARCHAR(110) NOT NULL,
  "media_url" VARCHAR(110)
);
