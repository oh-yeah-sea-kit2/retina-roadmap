import Foundation

// MARK: - API Client

/// 網膜色素変性症ロードマップAPIクライアント
@MainActor
class RetinaRoadmapAPI: ObservableObject {

    // MARK: - Properties

    static let shared = RetinaRoadmapAPI()

    private let baseURL = "https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1"
    private let session: URLSession
    private let decoder: JSONDecoder

    // MARK: - Published Properties

    @Published var programs: [ClinicalProgram] = []
    @Published var timeline: Timeline?
    @Published var statistics: Statistics?
    @Published var isLoading = false
    @Published var error: Error?

    // MARK: - Initialization

    private init() {
        let config = URLSessionConfiguration.default
        config.requestCachePolicy = .returnCacheDataElseLoad
        config.urlCache = URLCache(
            memoryCapacity: 50_000_000, // 50 MB
            diskCapacity: 100_000_000   // 100 MB
        )
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
        self.decoder.dateDecodingStrategy = .iso8601
    }

    // MARK: - Public API

    /// 全治療プログラムを取得
    func fetchPrograms() async throws -> [ClinicalProgram] {
        let url = URL(string: "\(baseURL)/programs.json")!
        let response: ProgramsResponse = try await fetch(from: url)

        DispatchQueue.main.async {
            self.programs = response.programs
        }

        return response.programs
    }

    /// 個別プログラムの詳細を取得
    func fetchProgramDetail(id: String) async throws -> ProgramDetail {
        let url = URL(string: "\(baseURL)/programs/\(id).json")!
        return try await fetch(from: url)
    }

    /// タイムライン予測を取得
    func fetchTimeline() async throws -> Timeline {
        let url = URL(string: "\(baseURL)/timeline.json")!
        let timeline: Timeline = try await fetch(from: url)

        DispatchQueue.main.async {
            self.timeline = timeline
        }

        return timeline
    }

    /// 統計情報を取得
    func fetchStatistics() async throws -> Statistics {
        let url = URL(string: "\(baseURL)/statistics.json")!
        let stats: Statistics = try await fetch(from: url)

        DispatchQueue.main.async {
            self.statistics = stats
        }

        return stats
    }

    /// APIメタ情報を取得
    func fetchMeta() async throws -> APIMeta {
        let url = URL(string: "\(baseURL)/meta.json")!
        return try await fetch(from: url)
    }

    // MARK: - Private Methods

    private func fetch<T: Decodable>(from url: URL) async throws -> T {
        isLoading = true
        defer { isLoading = false }

        do {
            let (data, response) = try await session.data(from: url)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }

            guard 200...299 ~= httpResponse.statusCode else {
                throw APIError.httpError(httpResponse.statusCode)
            }

            return try decoder.decode(T.self, from: data)

        } catch let error as APIError {
            self.error = error
            throw error
        } catch {
            let apiError = APIError.decodingError(error)
            self.error = apiError
            throw apiError
        }
    }
}

// MARK: - Data Models

/// 治療プログラム概要
struct ClinicalProgram: Codable, Identifiable {
    let id: String
    let name: String
    let company: String
    let currentPhase: String
    let status: String
    let modality: String
    let target: String
    let predictedApproval: PredictedApproval?
    let summary: String
    let priority: Int
    let lastUpdate: String?

    enum CodingKeys: String, CodingKey {
        case id, name, company, status, modality, target, summary, priority
        case currentPhase = "current_phase"
        case predictedApproval = "predicted_approval"
        case lastUpdate = "last_update"
    }
}

/// 予測承認時期
struct PredictedApproval: Codable {
    let fda: String?
    let japan: String?
    let europe: String?
}

/// プログラム詳細
struct ProgramDetail: Codable {
    let id: String
    let company: String
    let currentPhase: String
    let status: String
    let keyDates: KeyDates
    let trialIds: [String]
    let modality: String
    let target: String
    let regulatory: [String]
    let recentUpdates: [Update]
    let notes: String
    let predictedApproval: PredictedApproval?
    let links: Links?

    enum CodingKeys: String, CodingKey {
        case id, company, status, modality, target, regulatory, notes, links
        case currentPhase = "current_phase"
        case keyDates = "key_dates"
        case trialIds = "trial_ids"
        case recentUpdates = "recent_updates"
        case predictedApproval = "predicted_approval"
    }
}

/// 重要日程
struct KeyDates: Codable {
    let phase3Start: String?
    let phase3Completion: String?
    let blaSubmissionStart: String?
    let expectedBlaCompletion: String?

    enum CodingKeys: String, CodingKey {
        case phase3Start = "phase3_start"
        case phase3Completion = "phase3_completion"
        case blaSubmissionStart = "bla_submission_start"
        case expectedBlaCompletion = "expected_bla_completion"
    }
}

/// 最新情報
struct Update: Codable, Identifiable {
    var id: String { date + event }
    let date: String
    let event: String
    let source: String
    let importance: String?
}

/// リンク
struct Links: Codable {
    let companyWebsite: String?
    let clinicalTrialsGov: String?

    enum CodingKeys: String, CodingKey {
        case companyWebsite = "company_website"
        case clinicalTrialsGov = "clinicaltrials_gov"
    }
}

/// タイムライン予測
struct Timeline: Codable {
    let metadata: TimelineMetadata
    let predictions: Predictions
}

struct TimelineMetadata: Codable {
    let simulationDate: String
    let method: String
    let confidenceInterval: Double

    enum CodingKeys: String, CodingKey {
        case method
        case simulationDate = "simulation_date"
        case confidenceInterval = "confidence_interval"
    }
}

struct Predictions: Codable {
    let firstApproval: FirstApproval
    let byRegion: [String: RegionalPrediction]

    enum CodingKeys: String, CodingKey {
        case firstApproval = "first_approval"
        case byRegion = "by_region"
    }
}

struct FirstApproval: Codable {
    let program: String
    let medianDate: String
    let confidence90: ConfidenceInterval
    let probabilityByYear: [String: Double]

    enum CodingKeys: String, CodingKey {
        case program
        case medianDate = "median_date"
        case confidence90 = "confidence_90"
        case probabilityByYear = "probability_by_year"
    }
}

struct ConfidenceInterval: Codable {
    let lower: String
    let upper: String
}

struct RegionalPrediction: Codable {
    let medianApprovalYear: Int
    let delayYears: Int?
    let programs: [String]
    let description: String

    enum CodingKeys: String, CodingKey {
        case programs, description
        case medianApprovalYear = "median_approval_year"
        case delayYears = "delay_years"
    }
}

/// 統計情報
struct Statistics: Codable {
    let overview: Overview
    let successRates: [String: SuccessRate]
    let modalityBreakdown: [String: Int]
    let statusBreakdown: [String: Int]
    let regionalStatus: RegionalStatus

    enum CodingKeys: String, CodingKey {
        case overview
        case successRates = "success_rates"
        case modalityBreakdown = "modality_breakdown"
        case statusBreakdown = "status_breakdown"
        case regionalStatus = "regional_status"
    }
}

struct Overview: Codable {
    let totalPrograms: Int
    let activePrograms: Int
    let phaseDistribution: [String: Int]
    let lastUpdated: String

    enum CodingKeys: String, CodingKey {
        case lastUpdated = "last_updated"
        case totalPrograms = "total_programs"
        case activePrograms = "active_programs"
        case phaseDistribution = "phase_distribution"
    }
}

struct SuccessRate: Codable {
    let successRate: Double
    let successCount: Int
    let totalCount: Int
    let confidence: String

    enum CodingKeys: String, CodingKey {
        case confidence
        case successRate = "success_rate"
        case successCount = "success_count"
        case totalCount = "total_count"
    }
}

struct RegionalStatus: Codable {
    let fdaApproved: Int
    let fdaUnderReview: Int
    let japanApproved: Int
    let europeApproved: Int

    enum CodingKeys: String, CodingKey {
        case fdaApproved = "fda_approved"
        case fdaUnderReview = "fda_under_review"
        case japanApproved = "japan_approved"
        case europeApproved = "europe_approved"
    }
}

/// APIメタ情報
struct APIMeta: Codable {
    let apiVersion: String
    let lastUpdated: String
    let endpoints: [Endpoint]
    let dataSources: [String: String]
    let updateFrequency: [String: String]
    let repository: String
    let documentation: String

    enum CodingKeys: String, CodingKey {
        case endpoints, repository, documentation
        case apiVersion = "api_version"
        case lastUpdated = "last_updated"
        case dataSources = "data_sources"
        case updateFrequency = "update_frequency"
    }
}

struct Endpoint: Codable {
    let path: String
    let description: String
    let method: String
    let example: String?
}

/// プログラム一覧レスポンス
struct ProgramsResponse: Codable {
    let metadata: ProgramsMetadata
    let programs: [ClinicalProgram]
}

struct ProgramsMetadata: Codable {
    let lastUpdated: String
    let totalCount: Int
    let apiVersion: String
    let generatedAt: String

    enum CodingKeys: String, CodingKey {
        case lastUpdated = "last_updated"
        case totalCount = "total_count"
        case apiVersion = "api_version"
        case generatedAt = "generated_at"
    }
}

// MARK: - Error Handling

enum APIError: LocalizedError {
    case invalidResponse
    case httpError(Int)
    case decodingError(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "無効なレスポンスです"
        case .httpError(let code):
            return "HTTPエラー: \(code)"
        case .decodingError(let error):
            return "データ解析エラー: \(error.localizedDescription)"
        case .networkError(let error):
            return "ネットワークエラー: \(error.localizedDescription)"
        }
    }
}

// MARK: - Usage Example in SwiftUI

/*
 使用例:

 import SwiftUI

 struct ProgramsListView: View {
     @StateObject private var api = RetinaRoadmapAPI.shared

     var body: some View {
         NavigationView {
             List {
                 ForEach(api.programs) { program in
                     NavigationLink(destination: ProgramDetailView(programId: program.id)) {
                         ProgramRowView(program: program)
                     }
                 }
             }
             .navigationTitle("治療プログラム")
             .task {
                 do {
                     try await api.fetchPrograms()
                 } catch {
                     print("エラー: \(error)")
                 }
             }
             .overlay {
                 if api.isLoading {
                     ProgressView()
                 }
             }
         }
     }
 }

 struct ProgramRowView: View {
     let program: ClinicalProgram

     var body: some View {
         VStack(alignment: .leading, spacing: 4) {
             HStack {
                 Text(program.name)
                     .font(.headline)

                 Spacer()

                 PriorityBadge(priority: program.priority)
             }

             Text(program.company)
                 .font(.subheadline)
                 .foregroundColor(.secondary)

             HStack {
                 Label(program.currentPhase, systemImage: "flask")
                     .font(.caption)

                 if let approval = program.predictedApproval?.fda {
                     Label("FDA予測: \(approval)", systemImage: "calendar")
                         .font(.caption)
                 }
             }
             .foregroundColor(.blue)
         }
         .padding(.vertical, 4)
     }
 }

 struct PriorityBadge: View {
     let priority: Int

     var body: some View {
         Text(priorityText)
             .font(.caption2)
             .padding(.horizontal, 8)
             .padding(.vertical, 2)
             .background(priorityColor)
             .foregroundColor(.white)
             .cornerRadius(4)
     }

     private var priorityText: String {
         switch priority {
         case 1: return "最優先"
         case 2: return "重要"
         case 3: return "中"
         case 4: return "低"
         default: return "その他"
         }
     }

     private var priorityColor: Color {
         switch priority {
         case 1: return .red
         case 2: return .orange
         case 3: return .blue
         default: return .gray
         }
     }
 }

 struct ProgramDetailView: View {
     let programId: String
     @State private var detail: ProgramDetail?
     @State private var isLoading = false

     var body: some View {
         ScrollView {
             if let detail = detail {
                 VStack(alignment: .leading, spacing: 16) {
                     // 基本情報
                     Section("基本情報") {
                         InfoRow(label: "会社", value: detail.company)
                         InfoRow(label: "フェーズ", value: detail.currentPhase)
                         InfoRow(label: "ステータス", value: detail.status)
                         InfoRow(label: "治療法", value: detail.modality)
                     }

                     // 最新情報
                     Section("最新情報") {
                         ForEach(detail.recentUpdates) { update in
                             UpdateRow(update: update)
                         }
                     }

                     // 予測承認時期
                     if let approval = detail.predictedApproval {
                         Section("予測承認時期") {
                             if let fda = approval.fda {
                                 InfoRow(label: "米国 (FDA)", value: fda)
                             }
                             if let japan = approval.japan {
                                 InfoRow(label: "日本", value: japan)
                             }
                             if let europe = approval.europe {
                                 InfoRow(label: "欧州 (EMA)", value: europe)
                             }
                         }
                     }

                     // 詳細説明
                     Section("詳細") {
                         Text(detail.notes)
                             .font(.body)
                     }
                 }
                 .padding()
             } else if isLoading {
                 ProgressView()
             }
         }
         .navigationTitle(programId)
         .task {
             await loadDetail()
         }
     }

     private func loadDetail() async {
         isLoading = true
         defer { isLoading = false }

         do {
             detail = try await RetinaRoadmapAPI.shared.fetchProgramDetail(id: programId)
         } catch {
             print("エラー: \(error)")
         }
     }
 }

 struct InfoRow: View {
     let label: String
     let value: String

     var body: some View {
         HStack {
             Text(label)
                 .foregroundColor(.secondary)
             Spacer()
             Text(value)
                 .bold()
         }
     }
 }

 struct UpdateRow: View {
     let update: Update

     var body: some View {
         VStack(alignment: .leading, spacing: 4) {
             HStack {
                 Text(update.date)
                     .font(.caption)
                     .foregroundColor(.secondary)

                 if let importance = update.importance {
                     ImportanceBadge(importance: importance)
                 }
             }

             Text(update.event)
                 .font(.body)

             Text("出典: \(update.source)")
                 .font(.caption)
                 .foregroundColor(.secondary)
         }
         .padding(.vertical, 4)
     }
 }

 struct ImportanceBadge: View {
     let importance: String

     var body: some View {
         Text(importance.uppercased())
             .font(.caption2)
             .padding(.horizontal, 6)
             .padding(.vertical, 2)
             .background(badgeColor)
             .foregroundColor(.white)
             .cornerRadius(3)
     }

     private var badgeColor: Color {
         switch importance.lowercased() {
         case "high": return .red
         case "medium": return .orange
         default: return .gray
         }
     }
 }
 */
