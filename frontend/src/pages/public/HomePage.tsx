/** Landing page */
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Sprout, TrendingUp, Handshake, Shield, ArrowRight, Users, Landmark, Newspaper, Store, ExternalLink } from 'lucide-react';

export function HomePage() {
  return (
    <div className="-mx-4 -mt-6">
      {/* Hero */}
      <section className="bg-gradient-to-br from-forest to-leaf text-white py-20 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <div className="flex justify-center mb-6">
            <Sprout className="w-16 h-16 text-gold" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">KrishiSetu</h1>
          <p className="text-xl md:text-2xl text-white/90 mb-2">A Complete Ecosystem for Agriculture</p>
          <p className="text-lg text-white/70 max-w-2xl mx-auto mb-8">
            Connecting farmers directly with retailers, wholesalers, food processors and institutional buyers across Maharashtra.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" variant="secondary">
                Get Started <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/marketplace">
              <Button size="lg" variant="outline" className="!border-white !text-white hover:!bg-white/10">
                Browse Marketplace
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 bg-cream">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-forest mb-12">How KrishiSetu Works</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { icon: <Sprout className="w-8 h-8" />, title: 'List Your Crops', desc: 'Farmers list their produce with quantity, quality, and asking price.' },
              { icon: <TrendingUp className="w-8 h-8" />, title: 'Compare Prices', desc: 'Access market price data and compare offers with a net-proceeds calculator.' },
              { icon: <Handshake className="w-8 h-8" />, title: 'Negotiate Deals', desc: 'Use Digital Deal Rooms with video calls and real-time chat to negotiate.' },
              { icon: <Shield className="w-8 h-8" />, title: 'Secure Agreements', desc: 'Document agreements with clear terms, delivery, and payment details.' },
            ].map((f, i) => (
              <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
                <div className="w-16 h-16 bg-pale-green text-forest rounded-full flex items-center justify-center mx-auto mb-4">
                  {f.icon}
                </div>
                <h3 className="font-semibold text-lg mb-2 text-dark-text">{f.title}</h3>
                <p className="text-sm text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Working modules */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-forest mb-3">Explore KrishiSetu</h2>
          <p className="text-center text-gray-600 mb-10">Open a module to use its available features and official information sources.</p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { to: '/marketplace', icon: <Store className="h-7 w-7" />, title: 'Farmer Marketplace', desc: 'Search crop listings, compare asking prices and create listings after signing in.', label: 'Open marketplace' },
              { to: '/market-prices', icon: <TrendingUp className="h-7 w-7" />, title: 'Mandi Market Prices', desc: 'Filter saved official mandi records by crop, state, district and market.', label: 'Check prices' },
              { to: '/farmer-community', icon: <Users className="h-7 w-7" />, title: 'Farmer Community', desc: 'Find crop and regional groups, join discussions and publish farming posts.', label: 'Open community' },
              { to: '/schemes', icon: <Landmark className="h-7 w-7" />, title: 'Government Schemes', desc: 'Browse scheme cards and follow each official application or information link.', label: 'Explore schemes' },
              { to: '/news', icon: <Newspaper className="h-7 w-7" />, title: 'Agriculture News', desc: 'Read source-linked agriculture updates and open the original publisher article.', label: 'Read news' },
              { to: '/auctions', icon: <Handshake className="h-7 w-7" />, title: 'Auctions & Trade', desc: 'Explore the app’s auction and buyer-request workflows.', label: 'Explore trade' },
            ].map((item) => (
              <Link key={item.to} to={item.to} className="group rounded-2xl border border-gray-200 bg-cream p-5 shadow-sm transition hover:-translate-y-1 hover:border-leaf hover:shadow-md">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-pale-green text-forest">{item.icon}</div>
                <h3 className="text-lg font-bold text-forest">{item.title}</h3>
                <p className="mt-2 min-h-12 text-sm leading-6 text-gray-600">{item.desc}</p>
                <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-green-800">{item.label} <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" /></span>
              </Link>
            ))}
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-sm">
            <a className="inline-flex items-center gap-1 font-semibold text-green-800 underline" href="https://agmarknet.gov.in/" target="_blank" rel="noreferrer">Official Agmarknet portal <ExternalLink className="h-3.5 w-3.5" /></a>
            <a className="inline-flex items-center gap-1 font-semibold text-green-800 underline" href="https://www.myscheme.gov.in/" target="_blank" rel="noreferrer">Official myScheme portal <ExternalLink className="h-3.5 w-3.5" /></a>
            <a className="inline-flex items-center gap-1 font-semibold text-green-800 underline" href="https://pib.gov.in/" target="_blank" rel="noreferrer">Press Information Bureau <ExternalLink className="h-3.5 w-3.5" /></a>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-pale-green">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-forest mb-4">Ready to transform your agricultural trade?</h2>
          <p className="text-gray-700 mb-8">Join farmers and buyers who are discovering better prices and building lasting trade relationships.</p>
          <Link to="/register"><Button size="lg">Create Free Account</Button></Link>
        </div>
      </section>
    </div>
  );
}
