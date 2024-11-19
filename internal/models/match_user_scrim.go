package models

type MatchUserScrim struct {
	PlayerId     uint64  `gorm:"primaryKey;autoIncrement:false " json:"player_id"`
	Player       User    `gorm:"foreignKey:PlayerId" json:"player"`
	MatchId      uint64  `gorm:"primaryKey;autoIncrement:false" json:"match_id"`
	Match        Matches `gorm:"foreignKey:MatchId" json:"match"`
	Score        uint64  `json:"score"`
	IsBlue       bool    `gorm:"default:false" json:"is_blue"`
	RatingChange float64 `gorm:"default:null" json:"rating_change"`
}
