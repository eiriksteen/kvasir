import Image from 'next/image';
import Link from 'next/link';

export default function PublicHeader() {

	const navItems = [
		{ name: 'Product', path: '/products' },
		{ name: 'Contact', path: '/contact' },
	];

	return (
		<header className="fixed top-0 left-0 right-0 z-50 bg-black">
			<div className="mx-auto px-4 sm:px-6 lg:px-6">
				<div className="flex items-center justify-between h-12">
				<div className="flex-shrink-0">
					<Link href="/">
						<div className="relative w-[30px] h-[30px]">
							<Image
								src="/miyaicon.png"
								alt="Miya logo"
								fill
								priority
								className="object-contain"
							/>
						</div>
					</Link>
				</div>
				
				<nav className="hidden md:flex space-x-8">
					{navItems.map((item) => (
						<Link
							key={item.path}
							href={item.path}
							className={`${
								'text-gray-600 hover:text-[rgb(104,16,255)]'
							} px-3 py-2 text-sm font-medium transition-colors duration-200`}
						>
							{item.name}
						</Link>
					))}
				</nav>

				<div className="flex items-center space-x-4">
					<Link
						href="/login"
						className="hidden md:inline-flex items-center justify-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-[rgb(104,16,255)] hover:bg-[rgb(104,16,255)]/90 transition-colors duration-200"
					>
						Get Started
					</Link>
					
					<button className="md:hidden p-2 rounded-md text-gray-700 hover:text-[rgb(104,16,255)] hover:bg-gray-100">
						<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
						</svg>
					</button>
				</div>
			</div>
		</div>
	</header>
	);
} 