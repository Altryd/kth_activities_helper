package models

type MatchUserScrim struct {
	PlayerId uint64 `gorm:"primaryKey;autoIncrement:false" json:"player_id"`
	MatchId  uint64 `gorm:"primaryKey;autoIncrement:false" json:"match_id"`
	Score    uint64 `json:"score"`
	IsBlue   bool   `gorm:"default:false" json:"is_blue"`
}
