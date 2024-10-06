package database

import (
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"kth_activities_helper/internal/models"
	"log"
)

func Init() *gorm.DB {
	dsn := "host=localhost user=postgres password=123 dbname=kth_activities_helper port=5432 sslmode=disable"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatal(err)
	}
	db.AutoMigrate(&models.MatchType{}, &models.Matches{}, &models.User{}, &models.MatchUserScrim{})
	return db
}
